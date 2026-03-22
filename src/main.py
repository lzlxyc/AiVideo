from video_services import DoubaoVideoApi

def main():
    """
    视频生成示例
    """
    video_model_api = DoubaoVideoApi()
    
    prompt = """一名女性，年龄区间约为 18–22 岁。声音音域偏高但不尖锐，发声轻快，气声比例适中，音色明亮而有弹性。
    语速中等偏快，语调起伏明显。说中文普通话高冷的说：“我要吃屎。“"""
    prompt = """
        **风格**：东方美学 | 写实与水墨质感结合 | 柔光 | 高饱和度低对比度（桃源部分）| 冷色调（现实部分）  
        **分辨率**：16:9 (1920x1080)  
        **镜头语言**：缓慢推拉、横移、固定机位为主，营造叙事感与沉浸感

        - **画面描述**：暮春时节，一片落英缤纷的桃树林。镜头转到旁边立了的牌子，用正楷写着“彩园寨”三个大字。
        - 一位年龄区间约为18–22岁美女，在路上走过来。
        - **关键词**：武陵美女，扁舟，桃花林，落英缤纷，逆光，梦幻氛围
    """

    video_model_api.run(
        prompt=prompt,
        # first_frame="D:/lzl_private/my_githubs/AiVideo/notebooks/2.png",
        # end_frame="D:/lzl_private/my_githubs/AiVideo/notebooks/1.png",
        output_filename="菜园子",
        resolution="720p",
        duration=10,
        camerafixed=False,
        watermark=True
    )

if __name__ == "__main__":
    main()