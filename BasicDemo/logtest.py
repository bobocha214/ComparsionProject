from loguru import logger

# 自定义筛选器函数，用于判断是否记录日志消息
def custom_filter(record):
    # 如果消息与上一条消息相同，返回False，表示丢弃该消息
    if hasattr(custom_filter, "last_message") and custom_filter.last_message == record["message"]:
        return False
    custom_filter.last_message = record["message"]
    return True

# 创建一个输出目标（sink）为日志文件，并将自定义筛选器添加到它上面
logger.add("error.log", filter=custom_filter)

# 记录一些日志消息
for i in range(5):
    logger.info("这是一条测试日志消息")

# 关闭Loguru的日志记录器，以确保所有消息都被写入文件
logger.remove()

# 在同一文件上继续记录更多日志消息
for i in range(5):
    logger.info("这是另一条测试日志消息")
