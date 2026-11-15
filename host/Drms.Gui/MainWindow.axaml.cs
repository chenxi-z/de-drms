using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Threading;
using ScottPlot;
using ScottPlot.Avalonia;

namespace Drms.Gui;

public partial class MainWindow : Window
{
    private readonly MainViewModel _vm = new();
    private DispatcherTimer? _plotTimer;

    /// <summary>
    /// 中文字体族名。ScottPlot 走 SkiaSharp，只会用**已注册**的字体；
    /// 光写字体名不够（系统字体不会自动被找到），必须先 AddFontFile。
    /// </summary>
    private static string _uiFont = "Microsoft YaHei";

    public MainWindow()
    {
        InitializeComponent();
        DataContext = _vm;

        RegisterCjkFont();
        _vm.RefreshPorts();
        ConfigurePlots();

        // 曲线刷新与数据采集解耦：50 ms 重绘一次就够了（20 Hz），
        // 比按事件重绘省 CPU，也避免高频重绘把 UI 线程压住。
        _plotTimer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(50) };
        _plotTimer.Tick += (_, _) => Render();
        _plotTimer.Start();

        _vm.PropertyChanged += (_, e) =>
        {
            if (e.PropertyName == nameof(MainViewModel.Connected) && _vm.Connected)
            {
                // 连上后把视口起点对齐到当前时间
                _startSeconds = null;
            }
        };

        // 命令行参数 --auto <COMx>：启动即连接。
        // 既是给自动化验证用的，也方便现场直接拉起来看数据。
        string[] args = Environment.GetCommandLineArgs();
        int autoIndex = Array.IndexOf(args, "--auto");
        if (autoIndex >= 0 && autoIndex + 1 < args.Length)
        {
            _vm.SelectedPort = args[autoIndex + 1];
            Opened += async (_, _) => await _vm.ConnectAsync();
        }
    }

    private double? _startSeconds;

    /// <summary>
    /// 把系统中文字体注册给 ScottPlot。
    ///
    /// 为什么必须显式注册：ScottPlot 5 用 SkiaSharp 渲染文字，而 SkiaSharp 默认
    /// 只知道内置的几种字体，找不到就退化成方框（界面上看到的"豆腐块"）。
    /// 把 ttc/ttf 文件喂给 Fonts.AddFontFile 之后，按族名指定才有效。
    /// </summary>
    private static void RegisterCjkFont()
    {
        var candidates = OperatingSystem.IsWindows()
            ? new (string Path, string Family)[]
              {
                  (@"C:\Windows\Fonts\msyh.ttc", "Microsoft YaHei"),
                  (@"C:\Windows\Fonts\msyhl.ttc", "Microsoft YaHei"),
                  (@"C:\Windows\Fonts\simhei.ttf", "SimHei"),
                  (@"C:\Windows\Fonts\simsun.ttc", "SimSun"),
              }
            : new (string Path, string Family)[]
              {
                  ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "Noto Sans CJK SC"),
                  ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", "WenQuanYi Zen Hei"),
              };

        foreach ((string path, string family) in candidates)
        {
            if (!File.Exists(path))
                continue;
            try
            {
                ScottPlot.Fonts.AddFontFile(family, path);
                _uiFont = family;
                Console.WriteLine($"已注册中文字体：{family} ← {path}");
                return;
            }
            catch (Exception ex)
            {
                // 换下一个候选，不要因为字体问题让整个界面起不来
                Console.WriteLine($"字体注册失败 {path}: {ex.Message}");
            }
        }
        Console.WriteLine("未找到可用中文字体，图上的中文会显示为方框");
    }

    private void ConfigurePlots()
    {
        // ScottPlot 默认字体不含中文字形，轴标题会渲染成豆腐块。
        // Plot.Font.Set() 会统一设置整个图的默认字体（标题/轴/图例/刻度），
        // 比逐个设 LabelFontName 可靠——后者只影响已经创建的那些 Label。
        foreach (AvaPlot plot in new[] { RatioPlot, OhmsPlot })
        {
            Plot p = plot.Plot;
            p.FigureBackground.Color = Colors.White;
            p.DataBackground.Color = Colors.White;
            p.Grid.MajorLineColor = Color.FromHex("#E5E7EB");
            p.Grid.MinorLineColor = Color.FromHex("#F3F4F6");
            p.Axes.Frameless(false);
            p.Axes.Color(Color.FromHex("#374151"));
            p.Legend.IsVisible = true;
            p.Font.Set(_uiFont);
        }

        RatioPlot.Plot.Title("R/R0（比值）");
        RatioPlot.Plot.YLabel("R/R0");
        OhmsPlot.Plot.Title("R（电阻）");
        OhmsPlot.Plot.YLabel("R (kOhm)");
        OhmsPlot.Plot.XLabel("相对连接时间 (s)");

        // 没有数据时不要显示 ±10 这种默认坐标，那会被误读成"数据接近 0"
        ShowPlaceholder(RatioPlot, "等待数据…");
        ShowPlaceholder(OhmsPlot, "等待数据…");
    }

    /// <summary>系统上可用的中文字体名。Win 用雅黑，Linux 用 Noto。</summary>
    private static string UiFont => _uiFont;

    private static void ShowPlaceholder(AvaPlot plot, string text)
    {
        plot.Plot.Clear();
        var txt = plot.Plot.Add.Text(text, 0.5, 0.5);
        txt.LabelFontName = _uiFont;
        txt.LabelFontSize = 14;
        txt.LabelFontColor = Color.FromHex("#9CA3AF");
        txt.Alignment = Alignment.MiddleCenter;
        plot.Plot.Axes.SetLimits(0, 1, 0, 1);
        plot.Refresh();
    }

    private void Render()
    {
        if (!_vm.Connected)
            return;

        List<CurvePoint> points = _vm.Points.ToList();
        if (points.Count < 2)
            return;

        _startSeconds ??= points[0].Seconds;

        // 用相对时间，避免横轴出现 1.27e6 这种没法读的数
        double[] xs = points.Select(p => p.Seconds - _startSeconds.Value).ToArray();

        // 主图：ratio。缺失值用 NaN，ScottPlot 会自动断开而不连线——
        // 这正是协议 §5 要求的"宁可不画也不插值"。
        double[] ratio = points.Select(p => p.Ratio ?? double.NaN).ToArray();
        bool hasRatio = ratio.Any(v => !double.IsNaN(v));
        RatioPlot.Plot.Clear();
        if (hasRatio)
        {
            var sig = RatioPlot.Plot.Add.Scatter(xs, ratio);
            sig.LegendText = "R/R0";
            sig.Color = Color.FromHex("#0072BD"); // MATLAB 默认蓝
            sig.MarkerSize = 0;
            sig.LineWidth = 1;
        }
        else
        {
            // 主图空白的常见原因是缺区间表（固件不发布 ratio）。
            // 直接说明原因，不要让人以为程序坏了。
            AddNote(RatioPlot, "R/R0 暂未发布：需要基线 R0 与区间表");
        }

        // 副图：R，换 kOhm 显示
        double[] ohms = points.Select(p => p.Ohms.HasValue ? p.Ohms.Value / 1000.0 : double.NaN).ToArray();
        bool hasOhms = ohms.Any(v => !double.IsNaN(v));
        OhmsPlot.Plot.Clear();
        if (hasOhms)
        {
            var sig = OhmsPlot.Plot.Add.Scatter(xs, ohms);
            sig.LegendText = "R (kOhm)";
            sig.Color = Color.FromHex("#D95319"); // MATLAB 默认橙
            sig.MarkerSize = 0;
            sig.LineWidth = 1;
        }
        else
        {
            AddNote(OhmsPlot, "R 暂未发布：检查激励与新鲜度");
        }

        if (hasRatio)
            RatioPlot.Plot.Axes.AutoScale();
        if (hasOhms)
            OhmsPlot.Plot.Axes.AutoScale();

        // 共享横轴：主图跟随副图的时间范围（副图总有值或已设占位范围）
        if (hasOhms && hasRatio)
            RatioPlot.Plot.Axes.SetLimitsX(OhmsPlot.Plot.Axes.GetLimits());

        RatioPlot.Refresh();
        OhmsPlot.Refresh();
    }

    /// <summary>在图上放一句说明文字，居中显示。</summary>
    private static void AddNote(AvaPlot plot, string text)
    {
        var txt = plot.Plot.Add.Text(text, 0.5, 0.5);
        txt.LabelFontName = _uiFont;
        txt.LabelFontSize = 13;
        txt.LabelFontColor = Color.FromHex("#9CA3AF");
        txt.Alignment = Alignment.MiddleCenter;
        plot.Plot.Axes.SetLimits(0, 1, 0, 1);
    }

    private void OnRefreshPorts(object? sender, RoutedEventArgs e) => _vm.RefreshPorts();

    private async void OnApplyConfig(object? sender, RoutedEventArgs e)
    {
        await _vm.ApplyConfigAsync();
    }

    private async void OnBuildBaseline(object? sender, RoutedEventArgs e)
    {
        await _vm.BuildBaselineAsync();
    }

    private void OnCancelBaseline(object? sender, RoutedEventArgs e) => _vm.CancelBaseline();

    private async void OnConnect(object? sender, RoutedEventArgs e)
    {
        try
        {
            await _vm.ConnectAsync();
        }
        catch (Exception ex)
        {
            // 界面层兜底：任何意外都要显式报出来，不能静默卡死
            Console.Error.WriteLine(ex);
            throw;
        }
    }

    private void OnDisconnect(object? sender, RoutedEventArgs e)
    {
        _vm.Disconnect();
        _startSeconds = null;
    }
}
