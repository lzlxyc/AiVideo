from src.video_model_api import VideoModelApi

def main():
    """
    视频生成示例
    """
    video_model_api = VideoModelApi()
    
    prompt = "一名女性，年龄区间约为 18–22 岁。声音音域偏高但不尖锐，发声轻快，气声比例适中，音色明亮而有弹性。语速中等偏快，语调起伏明显。情绪基线积极、外向，带有轻微兴奋感和青春活力。说中文普通话。她说：“如果有变动，记得第一时间跟我说一声。"
    # 测试视频生成
    video_model_api.run(
        prompt=prompt,
        output_filename="桃花源记",
        resolution="1080p",
        duration=10,
        camerafixed=False,
        watermark=True
    )

if __name__ == "__main__":
    main()