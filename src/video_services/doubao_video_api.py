import os
import time
import base64
import requests
import cv2
from tkinter import N
from dotenv import load_dotenv
from urllib.parse import urlparse
# 通过 pip install 'volcengine-python-sdk[ark]' 安装方舟SDK
from volcenginesdkarkruntime import Ark
from typing import Optional, List, Dict

load_dotenv()


class DoubaoVideoApi:
    def __init__(self, model=None, base_url=None, api_key=None):
        self.model = model or os.getenv('MODEL_NAME')
        self.client = Ark(
            # 此为默认路径，您可根据业务所在地域进行配置
            base_url=base_url or os.getenv('VIDEO_BASE_URL'),
            # 从环境变量中获取您的 API Key。此为默认方式，您可根据需要进行修改
            api_key=api_key or os.getenv('VIDEO_API_KEY')
        )
        print(f"======= MODEL INIT:{self.model} ========")
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

    def _text_content(self, prompt: str) -> dict:
        return {"type": "text", "text": prompt}

    def _img_content(self, img_path: str) -> dict:
        if 'http' not in img_path:
            with open(img_path, "rb") as image_file:
                base64_string = base64.b64encode(image_file.read()).decode("utf-8")
            url = f"data:image/jpeg;base64,{base64_string}"
        else:
            url = img_path
        
        return {
            "type": "image_url",
            "image_url": {"url": url}
        }

    def create_video(self, 
            prompt: str, first_frame: str, end_frame: str,
            output_filename: str = None, output_dir: str = "./outputs",
            resolution: str = "1080p", duration: int = 5,
            camerafixed: bool = False, watermark: bool = True,
        ) -> Dict:
        os.makedirs(output_dir, exist_ok=True)

        # base64_string = get_pic_base64("D:/lzl_private/my_githubs/AiVideo/notebooks/1.png")
        contents = [self._text_content(prompt)]
        print("========== 输入：", contents)
        if first_frame:
            contents.append(self._img_content(first_frame))
        if end_frame:
            contents.append(self._img_content(end_frame))

        print("----- create request -----")
        create_result = self.client.content_generation.tasks.create(
            model=self.model, # 模型 Model ID 已为您填入
            resolution=resolution,
            duration=duration,
            camera_fixed=camerafixed,
            watermark=watermark,
            content=contents
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
                # print(get_result)
                
                # 计算费用
                self._calculate_cost(get_result, resolution, duration)

                # 下载视频
                video_url = get_result.content.video_url
                if video_url:
                    local_path = self._download_video(
                        video_url, output_filename or task_id, output_dir
                        )
                    # print(f"Video saved to: {local_path}")
                return {
                    "status": status,
                    "video_path": local_path,
                }
            elif status == "failed":
                print("----- task failed -----")
                print(f"Error: {get_result.error}")
                return {
                    "status": status,
                    "error": get_result.error,
                }
            else:
                print(f"Current status: {status}, Retrying after 6 seconds...")
                time.sleep(6)


    def run(self, 
            prompt: str, first_frame: str= None , end_frame: str = None,
            output_filename: str = None, output_dir: str = "./outputs",
            resolution: str = "1080p", duration: int = 5,
            camerafixed: bool = False, watermark: bool = True,
        ) -> Dict:
        """
        生成视频并下载
        
        Args:
            prompt: 视频生成提示词
            first_frame: 首帧图片路径或URL（可选）
            end_frame: 尾帧图片路径或URL（可选）
            output_filename: 自定义输出文件名（不含扩展名），默认为任务ID
            output_dir: 视频保存目录，默认为 ./outputs
            resolution: 视频分辨率，可选 480p/720p/1080p，默认为 1080p
            duration: 视频时长（秒），默认为 5
            camerafixed: 是否固定相机，默认为 False
            watermark: 是否添加水印，默认为 True
        """
        stime = time.time()
        result = self.create_video(
            prompt, first_frame, end_frame, 
            output_filename, output_dir, 
            resolution, duration, camerafixed, watermark
        )    

        use_time = round(time.time() - stime, 4)
        print(f"==>> Total time: {use_time} seconds")
        print("=" * 50) 

        return result


    def _calculate_cost(
            self, result, resolution: str, duration: int
        ) -> None:
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


    def _download_video(
            self, video_url: str, filename: str, output_dir: str
        ) -> str:
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

    def extract_last_frame(self, video_path: str, output_dir: str = "./outputs") -> str:
        """
        提取视频的最后一帧并保存为图片
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            
        Returns:
            最后一帧图片的保存路径
        """
        print(f"Extracting last frame from {video_path}...")
        
        cap = cv2.VideoCapture(video_path)
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"Total frames: {total_frames}")
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
        ret, frame = cap.read()
        
        if not ret:
            cap.release()
            raise Exception(f"Failed to read frame from {video_path}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}_last_frame.jpg")
        
        cv2.imwrite(output_path, frame)
        cap.release()
        
        print(f"Last frame saved to: {output_path}")
        return output_path


if __name__ == "__main__":
    prompt = """一名女性，年龄区间约为 18–22 岁。声音音域偏高但不尖锐，发声轻快，气声比例适中，音色明亮而有弹性。
    语速中等偏快，语调起伏明显。说中文普通话高冷的说：“我要吃屎。“"""

    video_model_api = DoubaoVideoApi()
    video_model_api.run(
        prompt=prompt,
        # first_frame="D:/lzl_private/my_githubs/AiVideo/notebooks/2.png",
        # end_frame="D:/lzl_private/my_githubs/AiVideo/notebooks/1.png",
        output_filename="桃花源",
        resolution="720p",
        duration=10,
        camerafixed=False,
        watermark=True
    )