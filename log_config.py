import logging
import colorlog


def get_logger():
    # 创建logger对象
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # 创建控制台日志处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    # 创建文件日志处理器
    file_handler = logging.FileHandler(filename='./log.txt', encoding='GBK')
    file_handler.setLevel(logging.ERROR)
    # 定义颜色输出格式
    color_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s [%(levelname)s] %(module)s.%(funcName)s: %(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    # 将颜色输出格式添加到控制台日志处理器
    console_handler.setFormatter(color_formatter)
    # 设置文件日志处理器的日志格式
    file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(module)s->%(funcName)s: %(message)s'))
    # 移除默认的handler
    for handler in logger.handlers:
        logger.removeHandler(handler)
    # 将控制台日志处理器添加到logger对象
    logger.addHandler(console_handler)
    # 将文件日志处理器添加到logger对象
    logger.addHandler(file_handler)
    return logger


log = get_logger()
