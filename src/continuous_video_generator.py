"""
连贯视频生成脚本 - 根据剧本分段生成连贯视频

功能：
1. 解析剧本脚本
2. 分段生成视频（每段≤12秒）
3. 提取上一段视频的最后一帧
4. 作为下一段的首帧输入
"""

import os
import re
import ffmpeg
from video_services.doubao_video_api import DoubaoVideoApi



class ScriptParser:
    """
    剧本解析器
    """
    
    def __init__(self, script_text: str):
        """
        初始化剧本解析器
        
        Args:
            script_text: 剧本文本
        """
        self.script_text = script_text
        self.segments = self._parse_script()
    
    def _parse_script(self) -> list:
        """
        解析剧本，提取分段
        
        Returns:
            分段列表，每段包含序号和内容
        """
        segments = []
        
        lines = self.script_text.strip().split('#\n')
        
        for segment_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            segments.append({
                'num': segment_num,
                'content': line,
                'original': line
            })
              
            # match = re.match(r'^(\d+)[.、.](.+)', line)
            # if match:
            #     segment_num = int(match.group(1))
            #     content = match.group(2).strip()
            #     segments.append({
            #         'num': segment_num,
            #         'content': content,
            #         'original': line
            #     })
        
        return segments
    
    def get_segment(self, index: int) -> dict:
        """
        获取指定分段
        
        Args:
            index: 分段索引
            
        Returns:
            分段字典
        """
        if 0 <= index < len(self.segments):
            return self.segments[index]
        return None
    
    def get_all_segments(self) -> list:
        """
        获取所有分段
        
        Returns:
            分段列表
        """
        return self.segments
    
    def get_segment_count(self) -> int:
        """
        获取分段数量
        
        Returns:
            分段数量
        """
        return len(self.segments)


class ContinuousVideoGenerator:
    """
    连贯视频生成器
    """
    
    def __init__(self, video_api: DoubaoVideoApi):
        """
        初始化视频生成器
        
        Args:
            video_api: 豆包视频API实例
        """
        self.video_api = video_api
        self.output_dir = "./outputs/continuous"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_from_script(
        self,
        script_parser: ScriptParser,
        max_duration: int = 10,
        resolution: str = "720p",
        camerafixed: bool = False,
        watermark: bool = True
    ) -> list:
        """
        根据剧本生成连贯视频
        
        Args:
            script_parser: 剧本解析器
            max_duration: 每段视频最大时长（秒）
            resolution: 视频分辨率
            camerafixed: 是否固定相机
            watermark: 是否添加水印
            
        Returns:
            生成的视频文件路径列表
        """
        segments = script_parser.get_all_segments()
        total_segments = len(segments)
        
        print("=" * 60)
        print(f"开始连贯视频生成")
        print(f"剧本分段数: {total_segments}")
        print(f"每段最大时长: {max_duration}秒")
        print("=" * 60)
        
        video_paths = []
        last_frame_path = None
        
        for i, segment in enumerate(segments):
            print(f"\n{'=' * 60}")
            print(f"正在生成第 {segment['num']} 段视频 ({i+1}/{total_segments})")
            print(f"内容: {segment['content'][:50]}...")
            print(f"{'=' * 60}")
            
            output_filename = f"segment_{segment['num']:03d}"
            
            try:
                result = self.video_api.run(
                    prompt=segment['content'],
                    first_frame=last_frame_path,
                    output_filename=output_filename,
                    output_dir=self.output_dir,
                    resolution=resolution,
                    duration=max_duration,
                    camerafixed=camerafixed,
                    watermark=watermark
                )
                if video_path:=result.get('video_path', None):
                    video_paths.append(video_path)
                    
                    print(f"✓ 第 {segment['num']} 段视频生成成功: {video_path}")
                    
                    last_frame_path = self.video_api.extract_last_frame(
                        video_path,
                        self.output_dir
                    )
                    print(f"✓ 已提取最后一帧作为下一段首帧: {last_frame_path}")
                else:
                    print(f"✗ 第 {segment['num']} 段视频生成失败")
                    break
                    
            except Exception as e:
                print(f"✗ 第 {segment['num']} 段生成出错: {str(e)}")
                break
        
        print(f"\n{'=' * 60}")
        print(f"连贯视频生成完成！")
        print(f"成功生成: {len(video_paths)}/{total_segments} 段")
        print(f"{'=' * 60}")
        
        return video_paths
    
    def merge_videos(self, video_paths: list, output_filename: str = "merged_video.mp4") -> str:
        """
        合并多个视频文件
        
        Args:
            video_paths: 视频文件路径列表
            output_filename: 输出文件名
            
        Returns:
            合并后的视频路径
        """
        print(f"\n{'=' * 60}")
        print("开始合并视频...")
        print(f"{'=' * 60}")
        
        if not video_paths:
            print("没有视频需要合并")
            return None
        
        import cv2
        
        first_video = cv2.VideoCapture(video_paths[0])
        fps = int(first_video.get(cv2.CAP_PROP_FPS))
        width = int(first_video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(first_video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        output_path = os.path.join(self.output_dir, output_filename)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        for video_path in video_paths:
            print(f"正在处理: {os.path.basename(video_path)}")
            cap = cv2.VideoCapture(video_path)
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)
            
            cap.release()
        
        out.release()
        first_video.release()
        
        print(f"✓ 视频合并完成: {output_path}")
        print(f"{'=' * 60}")
        
        return output_path

    
    def merge_videos_v2(
            self, video_paths: list, 
            output_filename: str = "merged_video.mp4",
            mode: str = "smooth"
        ) -> str:
        """
        利用ffmpeg-python进行视频拼接：自然过渡
        
        Args:
            video_paths: 视频文件路径列表
            output_filename: 输出文件名
            mode: 拼接模式
                - "concat": 快速拼接，无重编码
                - "smooth": 平滑过渡，带淡入淡出效果
                - "xfade": XFade过渡，多种过渡效果
                
        Returns:
            合并后的视频路径
        """
        print(f"\n{'=' * 60}")
        print(f"开始合并视频 (FFmpeg-Python, 模式: {mode})...")
        print(f"{'=' * 60}")
        
        if not video_paths:
            print("没有视频需要合并")
            return None
        
        if len(video_paths) == 1:
            print("只有一个视频，无需合并")
            return video_paths[0]
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        try:
            if mode == "concat":
                return self._merge_concat(video_paths, output_path)
            elif mode == "smooth":
                return self._merge_smooth(video_paths, output_path)
            elif mode == "xfade":
                return self._merge_xfade(video_paths, output_path)
            else:
                print(f"未知的模式: {mode}，使用默认的smooth模式")
                return self._merge_smooth(video_paths, output_path)
                
        except ffmpeg.Error as e:
            print(f"✗ FFmpeg错误: {e.stderr.decode() if e.stderr else str(e)}")
            return None
        except Exception as e:
            print(f"✗ 合并过程出错: {str(e)}")
            return None
    
    def _merge_concat(self, video_paths: list, output_path: str) -> str:
        """
        快速拼接模式：无损拼接，速度快
        """
        print("使用快速拼接模式...")
        
        list_file = os.path.join(self.output_dir, "concat_list.txt")
        with open(list_file, 'w', encoding='utf-8') as f:
            for video_path in video_paths:
                abs_path = os.path.abspath(video_path).replace('\\', '/')
                f.write(f"file '{abs_path}'\n")
        
        for i, video_path in enumerate(video_paths, 1):
            print(f"  {i}. {os.path.basename(video_path)}")
        
        (
            ffmpeg
            .input(list_file, format='concat', safe=0)
            .output(output_path, c='copy')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        if os.path.exists(list_file):
            os.remove(list_file)
        
        print(f"✓ 视频合并完成: {output_path}")
        print(f"{'=' * 60}")
        return output_path
    
    def _merge_smooth(self, video_paths: list, output_path: str) -> str:
        """
        平滑过渡模式：带淡入淡出效果
        """
        print("使用平滑过渡模式...")
        
        streams = []
        for i, video_path in enumerate(video_paths):
            print(f"  {i+1}. {os.path.basename(video_path)}")
            
            abs_path = os.path.abspath(video_path).replace('\\', '/')
            
            probe = ffmpeg.probe(abs_path)
            duration = float(probe['streams'][0]['duration'])
            
            stream = ffmpeg.input(abs_path)
            
            if i == 0:
                video = stream.video.filter('fade', t='out', st=duration-0.5, d=0.5)
            elif i == len(video_paths) - 1:
                video = stream.video.filter('fade', t='in', st=0, d=0.5)
            else:
                video = (
                    stream.video
                    .filter('fade', t='in', st=0, d=0.5)
                    .filter('fade', t='out', st=duration-0.5, d=0.5)
                )
            
            streams.append(video)
        
        (
            ffmpeg
            .concat(*streams)
            .output(output_path)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        print(f"✓ 视频合并完成: {output_path}")
        print(f"{'=' * 60}")
        return output_path
    
    def _merge_xfade(self, video_paths: list, output_path: str) -> str:
        """
        XFade过渡模式：多种过渡效果（淡入淡出、滑动、擦除等）
        """
        print("使用XFade过渡模式...")
        
        transitions = [
            'fade', 'slideleft', 'slideright', 'slideup', 'slidedown',
            'circleopen', 'circleclose', 'rectcrop', 'distance',
            'pixelize', 'diagtl', 'diagtr', 'diagbl', 'diagbr',
            'hlslice', 'hrslice', 'vuslice', 'vdslice', 'dissolve'
        ]
        
        if len(video_paths) < 2:
            print("XFade至少需要2个视频")
            return None
        
        for i, video_path in enumerate(video_paths):
            print(f"  {i+1}. {os.path.basename(video_path)}")
        
        abs_path = os.path.abspath(video_paths[0]).replace('\\', '/')
        probe = ffmpeg.probe(abs_path)
        duration = float(probe['streams'][0]['duration'])
        
        transition_duration = 0.5
        offset = duration - transition_duration
        
        current = ffmpeg.input(abs_path).video
        
        for i in range(1, len(video_paths)):
            next_path = os.path.abspath(video_paths[i]).replace('\\', '/')
            next_probe = ffmpeg.probe(next_path)
            next_duration = float(next_probe['streams'][0]['duration'])
            
            transition = transitions[i % len(transitions)]
            
            next_video = ffmpeg.input(next_path).video
            
            current = ffmpeg.crossfade(
                current,
                next_video,
                duration=transition_duration,
                offset=offset,
                transition=transition
            )
            
            offset = next_duration - transition_duration
        
        (
            current
            .output(output_path)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        print(f"✓ 视频合并完成: {output_path}")
        print(f"{'=' * 60}")
        return output_path

def main():
    """
    主函数
    """
    
    script_text = """
    # 
    **风格**：东方美学 | 写实与水墨质感结合 | 柔光 | 高饱和度低对比度（桃源部分）| 冷色调（现实部分）  
    **分辨率**：16:9 (1920x1080)  
    **镜头语言**：缓慢推拉、横移、固定机位为主，营造叙事感与沉浸感

    #
    - **画面描述**：暮春时节，一片落英缤纷的桃树林。镜头转到旁边立了的牌子，用正楷写着"彩园寨"三个大字。
    - 一位年龄区间约为18–22岁美女，在路上走过来。
    - **关键词**：武陵美女，扁舟，桃花林，落英缤纷，逆光，梦幻氛围
    """

    a = """
    #
    - **画面描述**：美女走近牌子，伸手触摸"彩园寨"三个字。镜头特写她的手，手指轻轻划过字迹。
    - **关键词**：特写，手指，触摸，怀旧，细节

    #
    - **画面描述**：镜头拉远，美女转身走向桃林深处。夕阳透过树叶洒下金色光斑。
    - **关键词**：转身，背影，夕阳，金色光斑，唯美

    #
    - **画面描述**：美女在桃林中漫步，花瓣随风飘落。她抬头望向天空，眼神充满向往。
    - **关键词**：漫步，花瓣飘落，仰望，向往，诗意
    """
    
    parser = ScriptParser(script_text)
    
    print("剧本解析结果:")
    print("=" * 60)
    for segment in parser.get_all_segments():
        print(f"第 {segment['num']} 段: {segment['content']}")
    print("=" * 60)

    video_api = DoubaoVideoApi()
    generator = ContinuousVideoGenerator(video_api)
    
    video_paths = generator.generate_from_script(
        parser,
        max_duration=6,
        resolution="720p",
        camerafixed=False,
        watermark=True
    )
    
    if video_paths:
        generator.merge_videos_v2(video_paths, "taoyuan_story.mp4")


if __name__ == "__main__":
    # main()

    def _merge_smooth(video_paths: list, output_path: str) -> str:
        print("使用平滑过渡模式...")
        
        streams = []
        for i, video_path in enumerate(video_paths):
            print(f"  {i+1}. {os.path.basename(video_path)}")
            
            abs_path = os.path.abspath(video_path).replace('\\', '/')
            
            probe = ffmpeg.probe(abs_path)
            duration = float(probe['streams'][0]['duration'])
            
            stream = ffmpeg.input(abs_path)
            
            if i == 0:
                video = stream.video.filter('fade', t='out', st=duration-0.5, d=0.5)
            elif i == len(video_paths) - 1:
                video = stream.video.filter('fade', t='in', st=0, d=0.5)
            else:
                video = (
                    stream.video
                    .filter('fade', t='in', st=0, d=0.5)
                    .filter('fade', t='out', st=duration-0.5, d=0.5)
                )
            
            streams.append(video)
        
        (
            ffmpeg
            .concat(*streams)
            .output(output_path)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        print(f"✓ 视频合并完成: {output_path}")
        print(f"{'=' * 60}")


    video_paths = [
        'D:/lzl_private/my_githubs/AiVideo/outputs/continuous/segment_000.mp4',
        'D:/lzl_private/my_githubs/AiVideo/outputs/continuous/segment_001.mp4', ]
    output_path = 'D:/lzl_private/my_githubs/AiVideo/outputs/continuous/segment_merge.mp4'
    _merge_smooth(video_paths, output_path)





    