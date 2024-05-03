import time


def print_blank_line_and_delay():
    """打印空行，用于日志信息间的分隔

    [修复] 日志信息会和相邻的print/input语句显示在同一行的问题
    [优化] 不同函数/方法、每次循环打印的日志间空一行，避免密密麻麻连成一片很难看
    """
    time.sleep(0.5)
    print()
    time.sleep(0.5)