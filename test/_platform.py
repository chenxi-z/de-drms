"""测试用的平台适配层：C 扩展编译命令与共享库命名。

为什么需要它：
  绝大多数测试把仓库里的真实 C 源码编成共享库，再用 ctypes 加载来验证逻辑。
  这件事在 Linux 和 Windows 上的细节不同，原先每个测试文件各写一遍，于是
  同一份测试在 Windows 上会因为三件事集体失败：

    1. 编译器名：Linux 上是 `cc`，Windows 上通常只有 `gcc`。
    2. 产物扩展名：Linux 用 `.so`，Windows 必须用 `.dll` 才能真正被加载。
    3. 删除时机：Windows 不允许删除已被加载的 DLL，测试收尾必须先把
       ctypes 句柄释放掉，而 Linux 允许直接删。

  前两项集中成 `CC` / `EXT` 两个常量，第三项由 `release()` 统一处理。
  测试文件只负责业务断言，不再重复平台判断。

用法::

    from _platform import CC, EXT, release

    subprocess.run([CC, '-shared', '-fPIC', ..., '-o', str(p / f'mon{EXT}')], check=True)
    cls.lib = ctypes.CDLL(str(p / f'mon{EXT}'))

    @classmethod
    def tearDownClass(cls):
        release(cls)          # 先放掉 ctypes 句柄，Windows 才删得掉临时目录
        cls.tmp.cleanup()
"""
import ctypes as _ctypes
import gc
import os
import shutil
import sys

__all__ = ['CC', 'EXT', 'PYTHON', 'IS_WINDOWS', 'release', 'close', 'track']

IS_WINDOWS = sys.platform == 'win32'


def _pick_cc():
    """选一个能用的 C 编译器：显式覆盖 → cc → gcc → clang。"""
    override = os.environ.get('DRMS_CC')
    if override:
        return override
    for name in ('cc', 'gcc', 'clang'):
        if shutil.which(name):
            return name
    # 一个都没有时仍返回 'cc'，让失败信息指向最常见的那条路径。
    return 'cc'


#: 编译共享库用的 C 编译器。
CC = _pick_cc()

#: 共享库扩展名。Windows 的 ctypes 只认 `.dll`。
EXT = '.dll' if IS_WINDOWS else '.so'

#: "再起一个 Python 进程"时用的解释器。不要写死 `python3`：
#: Windows 上它可能只是应用商店的占位符，调用会静默失败（退出码 9009）。
PYTHON = sys.executable or ('python' if IS_WINDOWS else 'python3')


def release(*owners, names=('lib',)):
    """卸载这些对象（或其类）加载的 ctypes 共享库。

    为什么必须显式卸载：Windows 拒绝删除已映射到自己进程里的 DLL，
    `TemporaryDirectory.cleanup()` 于是报 `PermissionError: [WinError 5]`
    （Linux 允许删除已加载的 .so，所以那边从来没暴露这个问题）。

    为什么清引用不够：`ctypes.CDLL` 的 `__getattr__` 会把查到的函数缓存成
    `_FuncPtr`，而每个 `_FuncPtr` 又强引用着 DLL 对象；只要有一处
    `cls.lib.drms_xxx.argtypes = ...`，DLL 就活到进程结束。
    因此这里直接调 `FreeLibrary`，再清掉引用。

    `names` 用来覆盖"库没有存在 lib 属性里"的情况（例如同时加载两个库、
    分别叫 lib 和 roll 的测试）。
    """
    for owner in owners:
        if owner is None:
            continue
        objects = [owner] if isinstance(owner, type) else [type(owner), owner]
        for obj in objects:
            for lib in list(getattr(obj, '_tracked_libs', ()) or ()):
                _unload(lib)
            tracked = getattr(obj, '_tracked_libs', None)
            if isinstance(tracked, list):
                tracked.clear()
            for name in names:
                lib = getattr(obj, name, None)
                if isinstance(lib, _ctypes.CDLL):
                    _unload(lib)
                    try:
                        setattr(obj, name, None)
                    except (AttributeError, TypeError):
                        pass
    gc.collect()


def track(owner, *names):
    """记下 `owner` 上这些属性当前指向的库，供 `release()` 统一卸载。

    为什么需要它：测试里常见"同一个类每个用例加载一份干净副本"，或者
    "某个用例把 `self.lib` 换成另一个库"。后者会让先前那个库再也没有属性
    指向它，`release()` 只管当前值就会漏掉，Windows 下表现为
    `PermissionError: [WinError 5]` 删不掉临时目录。
    在加载处调用一次 `track(self, 'lib')`，收尾时就都能归还。
    """
    seen = getattr(owner, '_tracked_libs', None)
    if seen is None:
        seen = []
        owner._tracked_libs = seen
    for name in names:
        lib = getattr(owner, name, None)
        if isinstance(lib, _ctypes.CDLL) and lib not in seen:
            seen.append(lib)
    return owner


def close(*libs):
    """直接卸载若干 ctypes 库对象（用于只在一个测试方法里临时加载的库）。

    与 `release()` 的区别：`release()` 认的是"挂着 lib 属性的类/实例"，
    这里直接接收库本身，省去为了传参而造包装对象的麻烦。
    """
    for lib in libs:
        if isinstance(lib, _ctypes.CDLL):
            _unload(lib)
    gc.collect()


def _unload(lib):
    """尽力卸载一个 ctypes 库；失败不抛，避免清理错误盖住真正的断言失败。"""
    handle = getattr(lib, '_handle', None)
    if not handle:
        return
    try:
        import ctypes
        if IS_WINDOWS:
            ctypes.windll.kernel32.FreeLibrary(ctypes.c_void_p(handle))
        else:
            ctypes.CDLL(None).dlclose(ctypes.c_void_p(handle))
    except Exception:
        pass
