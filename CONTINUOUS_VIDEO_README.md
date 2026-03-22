# 连贯视频生成

根据剧本分段生成连贯视频，自动提取上一段视频的最后一帧作为下一段的首帧。

## 功能特性

1. **剧本解析**：自动解析编号格式的剧本（如 "1、xxx", "2、xxx"）
2. **分段生成**：每段视频时长可配置（默认10秒，最大12秒）
3. **帧提取**：自动提取上一段视频的最后一帧
4. **连贯生成**：使用上一段的最后一帧作为当前段的首帧
5. **视频合并**：可选合并所有分段为完整视频

## 安装依赖

```bash
pip install opencv-python
pip install volcengine-python-sdk[ark]
pip install python-dotenv
```

## 使用方法

### 1. 准备剧本

创建一个文本文件，按以下格式编写剧本：

```
1、第一段内容
2、第二段内容
3、第三段内容
...
```

### 2. 运行脚本

```bash
python src/continuous_video_generator.py
```

### 3. 自定义配置

修改 `continuous_video_generator.py` 中的 `main()` 函数：

```python
def main():
    script_text = """
    1、你的第一段内容
    2、你的第二段内容
    3、你的第三段内容
    """
    
    parser = ScriptParser(script_text)
    video_api = DoubaoVideoApi()
    generator = ContinuousVideoGenerator(video_api)
    
    video_paths = generator.generate_from_script(
        parser,
        max_duration=10,      # 每段最大时长（秒）
        resolution="720p",     # 视频分辨率
        camerafixed=False,     # 是否固定相机
        watermark=True          # 是否添加水印
    )
    
    # 可选：合并视频
    if video_paths:
        generator.merge_videos(video_paths, "output_video.mp4")
```

## 输出

生成的视频保存在 `./outputs/continuous/` 目录下：

- `segment_001.mp4` - 第1段视频
- `segment_002.mp4` - 第2段视频
- `segment_001_last_frame.jpg` - 第1段最后一帧
- `segment_002_last_frame.jpg` - 第2段最后一帧
- `merged_video.mp4` - 合并后的完整视频（可选）

## 注意事项

1. 每段视频时长不能超过12秒（豆包Seedance限制）
2. 建议每段时长设置为8-10秒，保证生成质量
3. 首帧图片会自动提取，无需手动准备
4. 如果某段生成失败，会停止后续生成

## 费用计算

脚本会自动计算每段视频的费用，包括：
- 模型名称
- 视频分辨率
- 视频时长
- 单价和总费用
