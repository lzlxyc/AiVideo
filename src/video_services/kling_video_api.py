"""
pip install PyJWT

可灵AI (Kling) 视频生成 API 调用脚本

文档参考: https://klingai.kuaishou.com/
API 文档: https://app.klingai.com/cn/dev/document-api/quickStart/userManual

鉴权方式: JWT (JSON Web Token) + Bearer Token
"""

import os
import time
import requests
import jwt
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()


class KlingVideoApi:
    """
    可灵AI视频生成API封装
    
    支持功能:
    - 文生视频 (Text-to-Video)
    - 图生视频 (Image-to-Video)
    - 首尾帧生视频 (Frame-to-Video)
    - 视频延长 (Video Extension)
    
    鉴权方式: 使用 Access Key 和 Secret Key 生成 JWT Token
    """
    
    def __init__(
        self,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        初始化可灵API客户端
        
        Args:
            access_key: Access Key，默认从环境变量 KLING_ACCESS_KEY 获取
            secret_key: Secret Key，默认从环境变量 KLING_SECRET_KEY 获取
            base_url: API基础URL，默认从环境变量 KLING_BASE_URL 获取
        """
        self.access_key = access_key or os.getenv('KLING_ACCESS_KEY')
        self.secret_key = secret_key or os.getenv('KLING_SECRET_KEY')
        self.base_url = base_url or os.getenv('KLING_BASE_URL', 'https://api.klingai.com')
        
        if not self.access_key or not self.secret_key:
            raise ValueError(
                "请设置 KLING_ACCESS_KEY 和 KLING_SECRET_KEY 环境变量\n"
                "或在初始化时传入 access_key 和 secret_key"
            )
    
    def _generate_jwt_token(self) -> str:
        """
        生成 JWT Token
        
        Returns:
            JWT Token 字符串
        """
        headers = {
            "alg": "HS256",
            "typ": "JWT"
        }
        payload = {
            "iss": self.access_key,
            "exp": int(time.time()) + 1800,
            "nbf": int(time.time()) - 5
        }
        token = jwt.encode(payload, self.secret_key, algorithm="HS256", headers=headers)
        return token
    
    def _get_headers(self) -> Dict[str, str]:
        """
        获取带 JWT Token 的请求头
        
        Returns:
            请求头字典
        """
        token = self._generate_jwt_token()
        print("API Token:", f'Bearer {token}')
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def _make_request(
        self,
        method: str,
        path: str,
        data: Dict[str, Any] = None,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求
        
        Args:
            method: HTTP 方法
            path: API 路径
            data: 请求体数据
            params: URL 参数
            
        Returns:
            响应数据
        """
        url = f"{self.base_url}{path}"
        headers = self._get_headers()
        
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=params)
        else:
            response = requests.post(url, headers=headers, json=data)
        
        response.raise_for_status()
        return response.json()
    
    def create_text_to_video(
        self,
        prompt: str,
        negative_prompt: str = "",
        duration: int = 5,
        aspect_ratio: str = "16:9",
        model: str = "kling-v1.5"
    ) -> dict:
        """
        文生视频 - 根据文本描述生成视频
        
        Args:
            prompt: 视频描述提示词
            negative_prompt: 负面提示词（不希望出现的内容）
            duration: 视频时长（秒），支持 5 或 10 秒
            aspect_ratio: 视频比例，可选 "16:9", "9:16", "1:1"
            model: 模型版本，可选 "kling-v1", "kling-v1.5", "kling-v1.6"
            
        Returns:
            包含任务ID的字典
        """
        path = "/v1/videos/text2video"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio
        }
        
        return self._make_request('POST', path, data=payload)
    
    def create_image_to_video(
        self,
        image_url: str,
        prompt: str = "",
        negative_prompt: str = "",
        duration: int = 5,
        model: str = "kling-v1.5"
    ) -> dict:
        """
        图生视频 - 根据图片生成视频
        
        Args:
            image_url: 图片URL地址（必须是公开可访问的URL）
            prompt: 视频描述提示词（可选）
            negative_prompt: 负面提示词
            duration: 视频时长（秒），支持 5 或 10 秒
            model: 模型版本
            
        Returns:
            包含任务ID的字典
        """
        path = "/v1/videos/image2video"
        
        payload = {
            "model": model,
            "image_url": image_url,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "duration": duration
        }
        
        return self._make_request('POST', path, data=payload)
    
    def create_video_with_end_frame(
        self,
        first_frame_url: str,
        end_frame_url: str,
        prompt: str = "",
        duration: int = 5,
        model: str = "kling-v1.5"
    ) -> dict:
        """
        首尾帧生视频 - 根据首帧和尾帧图片生成过渡视频
        
        Args:
            first_frame_url: 首帧图片URL
            end_frame_url: 尾帧图片URL
            prompt: 视频描述提示词
            duration: 视频时长（秒）
            model: 模型版本
            
        Returns:
            包含任务ID的字典
        """
        path = "/v1/videos/frame2video"
        
        payload = {
            "model": model,
            "first_frame_url": first_frame_url,
            "end_frame_url": end_frame_url,
            "prompt": prompt,
            "duration": duration
        }
        
        return self._make_request('POST', path, data=payload)
    
    def get_task_status(self, task_id: str) -> dict:
        """
        查询任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        path = f"/v1/videos/status/{task_id}"
        return self._make_request('GET', path)
    
    def wait_for_completion(
        self,
        task_id: str,
        poll_interval: int = 10,
        max_attempts: int = 60
    ) -> dict:
        """
        轮询等待任务完成
        
        Args:
            task_id: 任务ID
            poll_interval: 轮询间隔（秒）
            max_attempts: 最大轮询次数
            
        Returns:
            任务结果
        """
        for attempt in range(max_attempts):
            result = self.get_task_status(task_id)
            status = result.get('status', 'unknown')
            
            print(f"[{attempt + 1}/{max_attempts}] 任务状态: {status}")
            
            if status == 'completed':
                print("✓ 视频生成完成!")
                return result
            elif status == 'failed':
                error_msg = result.get('error_message', '未知错误')
                raise Exception(f"视频生成失败: {error_msg}")
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"等待超时，任务ID: {task_id}")
    
    def download_video(self, video_url: str, output_path: str) -> str:
        """
        下载生成的视频
        
        Args:
            video_url: 视频URL
            output_path: 保存路径
            
        Returns:
            保存的文件路径
        """
        response = requests.get(video_url, stream=True)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✓ 视频已保存: {output_path}")
        return output_path
    
    def run_text_to_video(
        self,
        prompt: str,
        output_filename: str = None,
        output_dir: str = "./outputs",
        **kwargs
    ) -> str:
        """
        完整的文生视频流程（提交任务 -> 等待完成 -> 下载视频）
        
        Args:
            prompt: 视频描述
            output_filename: 输出文件名
            output_dir: 输出目录
            **kwargs: 其他参数传递给 create_text_to_video
            
        Returns:
            保存的视频文件路径
        """
        print("=" * 50)
        print("开始文生视频任务")
        print(f"提示词: {prompt[:50]}...")
        print("=" * 50)
        
        # 提交任务
        result = self.create_text_to_video(prompt, **kwargs)
        task_id = result.get('task_id') or result.get('id')
        print(f"✓ 任务已提交，ID: {task_id}")
        
        # 等待完成
        final_result = self.wait_for_completion(task_id)
        
        # 下载视频
        video_url = final_result.get('video_url')
        if not video_url:
            raise Exception("未获取到视频URL")
        
        filename = output_filename or f"kling_{task_id}"
        output_path = os.path.join(output_dir, f"{filename}.mp4")
        
        return self.download_video(video_url, output_path)
    
    def run_image_to_video(
        self,
        image_url: str,
        prompt: str = "",
        output_filename: str = None,
        output_dir: str = "./outputs",
        **kwargs
    ) -> str:
        """
        完整的图生视频流程
        
        Args:
            image_url: 图片URL
            prompt: 视频描述
            output_filename: 输出文件名
            output_dir: 输出目录
            **kwargs: 其他参数
            
        Returns:
            保存的视频文件路径
        """
        print("=" * 50)
        print("开始图生视频任务")
        print(f"图片: {image_url}")
        print("=" * 50)
        
        result = self.create_image_to_video(image_url, prompt, **kwargs)
        task_id = result.get('task_id') or result.get('id')
        print(f"✓ 任务已提交，ID: {task_id}")
        
        final_result = self.wait_for_completion(task_id)
        video_url = final_result.get('video_url')
        
        filename = output_filename or f"kling_img_{task_id}"
        output_path = os.path.join(output_dir, f"{filename}.mp4")
        
        return self.download_video(video_url, output_path)


if __name__ == "__main__":
    # 使用示例
    api = KlingVideoApi()
    
    # 示例1: 文生视频
    api.run_text_to_video(
        prompt="一名宇航员在火星表面行走，背景是红色的沙丘和蓝色的地球",
        output_filename="astronaut_mars",
        duration=5,
        aspect_ratio="16:9",
        model="kling-v1.5"
    )
    
    # 示例2: 图生视频
    # api.run_image_to_video(
    #     image_url="https://example.com/image.jpg",
    #     prompt="让图片中的风景动起来，云朵飘动",
    #     output_filename="animated_scene",
    #     duration=5
    # )
    
    print("请先在 .env 文件中设置 KLING_ACCESS_KEY 和 KLING_SECRET_KEY，然后取消注释上面的示例代码运行")
