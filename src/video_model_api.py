import os
import time
import requests
from tkinter import N
from urllib.parse import urlparse
from dotenv import load_dotenv
# 通过 pip install 'volcengine-python-sdk[ark]' 安装方舟SDK
from volcenginesdkarkruntime import Ark

load_dotenv()

class VideoModelApi:
    def __init__(self, model=None, base_url=None, api_key=None):
        self.model = model or os.getenv('MODEL_NAME')
        self.client = Ark(
            # 此为默认路径，您可根据业务所在地域进行配置
            base_url=base_url or os.getenv('VIDEO_BASE_URL'),
            # 从环境变量中获取您的 API Key。此为默认方式，您可根据需要进行修改
            api_key=api_key or os.getenv('VIDEO_API_KEY')
        )
        
        # 计费配置（单位：元/秒）
        self.pricing = {
            "doubao-seedance-1-0-pro": {
                "480p": 0.008,
                "720p": 0.016,
                "1080p": 0.032,
            },
            "doubao-seedance-1-5-pro": {
                "480p": 0.012,
                "720p": 0.024,
                "1080p": 0.048,
            },
            "doubao-seedance-2-0-pro": {
                "480p": 0.016,
                "720p": 0.032,
                "1080p": 0.064,
            },
        }

    def create_video(self, prompt: str, 
            output_filename: str = None, 
            output_dir: str = "./outputs",
            resolution: str = "1080p",
            duration: int = 5,
            camerafixed: bool = False,
            watermark: bool = True,
        ) -> None:
        """
        生成视频并下载
        
        Args:
            prompt: 视频生成提示词
            output_filename: 自定义输出文件名（不含扩展名），默认为任务ID
            output_dir: 视频保存目录，默认为 ./output
        """
        os.makedirs(output_dir, exist_ok=True)

        print("----- create request -----")
        create_result = self.client.content_generation.tasks.create(
            model=self.model, # 模型 Model ID 已为您填入
            resolution=resolution,
            duration=duration,
            camera_fixed=camerafixed,
            watermark=watermark,
            content=[
                {
                    # 文本提示词与参数组合
                    "type": "text",
                    "text": prompt
                }
            ]
        )
        print(create_result)

        # 轮询查询部分
        print("----- polling task status -----")
        task_id = create_result.id

        while True:
            get_result = self.client.content_generation.tasks.get(task_id=task_id)
            status = get_result.status
            if status == "succeeded":
                print("----- task succeeded -----")
                print(get_result)
                
                # 下载视频
                video_url = get_result.content.video_url
                if video_url:
                    local_path = self._download_video(
                        video_url, output_filename or task_id, output_dir
                        )
                    print(f"Video saved to: {local_path}")
                return get_result
            elif status == "failed":
                print("----- task failed -----")
                print(f"Error: {get_result.error}")
                return get_result
            else:
                print(f"Current status: {status}, Retrying after 6 seconds...")
                time.sleep(6)


    def run(self, prompt: str, 
            output_filename: str = None, output_dir: str = "./outputs",
            resolution: str = "1080p", duration: int = 10,
            camerafixed: bool = False, watermark: bool = True,
        ) -> None:
        stime = time.time()
        result = self.create_video(
            prompt, output_filename, output_dir, 
            resolution, duration, camerafixed, watermark
        )    
        # 计算并输出费用
        if result and result.status == "succeeded":
            self._calculate_cost(result, resolution, duration)

        use_time = round(time.time() - stime, 4)
        print(f"==>> Total time: {use_time} seconds")
        print("=" * 50) 


    def _calculate_cost(self, result, resolution: str, duration: int) -> None:
        """
        计算并输出本次调用的费用
        
        Args:
            result: 任务结果对象
            resolution: 视频分辨率
            duration: 视频时长（秒）
        """
        # 从模型ID中提取模型名称（去掉日期后缀）
        model_name = result.model
        for model_key in self.pricing.keys():
            if model_key in model_name:
                model_name = model_key
                break
        
        # 获取实际生成的视频时长
        actual_duration = result.duration if hasattr(result, 'duration') else duration
        
        # 获取单价
        model_pricing = self.pricing.get(model_name, self.pricing["doubao-seedance-1-0-pro"])
        price_per_second = model_pricing.get(resolution, model_pricing["1080p"])
        
        # 计算总费用
        total_cost = actual_duration * price_per_second
        
        # 输出费用信息
        print("=" * 50)
        print("费用统计")
        print("=" * 50)
        print(f"模型: {model_name}")
        print(f"分辨率: {resolution}")
        print(f"视频时长: {actual_duration} 秒")
        print(f"单价: ¥{price_per_second:.3f} / 秒")
        print(f"本次费用: ¥{total_cost:.3f}")
        print("=" * 50)


    def _download_video(self, video_url: str, filename: str, output_dir: str) -> str:
        """
        下载视频到本地
        
        Args:
            video_url: 视频URL
            filename: 保存的文件名（不含扩展名）
            output_dir: 保存目录
            
        Returns:
            本地文件路径
        """
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 从URL获取文件扩展名
        parsed_url = urlparse(video_url)
        ext = os.path.splitext(parsed_url.path)[1] or ".mp4"
        
        # 构建完整路径
        local_path = os.path.join(output_dir, f"{filename}{ext}")
        
        # 下载视频
        print(f"Downloading video from {video_url}...")
        response = requests.get(video_url, stream=True)
        response.raise_for_status()
        
        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Download completed: {local_path}")
        return local_path