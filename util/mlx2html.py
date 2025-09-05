from contextlib import contextmanager
from typing import Iterator
import os

import matlab.engine

def mlx2html(eng, mlx_input_path, html_output_path: matlab.engine.MatlabEngine):
    mlx_input_path = os.path.abspath(mlx_input_path)
    html_output_path = os.path.abspath(html_output_path)
    eng.matlab.internal.liveeditor.openAndConvert(mlx_input_path, html_output_path, nargout=0)

def rel_path2abs_path(rel_path: str) -> str:
    return  os.path.abspath(rel_path)

@contextmanager
def matlab_engine() -> Iterator[matlab.engine.MatlabEngine]:
    """
    MATLAB引擎的上下文管理器，自动处理构建引擎和关闭引擎
    
    输出:
        matlab.engine.MatlabEngine: MATLAB引擎实例
        
    Example:
        with matlab_engine() as eng:
            result = eng.sqrt(4.0)
            print(result)  # 自动调用eng.quit()
    """
    eng = None
    try:
        eng = matlab.engine.start_matlab()
        print("MATLAB engine started")
        yield eng
    finally:
        if eng is not None:
            eng.quit()
            print("MATLAB engine stopped")