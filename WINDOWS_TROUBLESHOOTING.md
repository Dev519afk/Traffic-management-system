# Windows troubleshooting — PyTorch / CUDA App Control

## Known issue on the user's laptop

The previous project encountered:

```text
OSError: [WinError 4551] An Application Control policy has blocked this file.
...torch\lib\c10_cuda.dll
```

Windows Code Integrity event IDs **3077** and **3033** reported a policy block involving `python3.12.exe` from a Microsoft Store Python installation. The model, tracker YAML and Python script did not cause this security rejection.

**Do not disable App Control or relax Windows security to run the project.** Reinstalling CUDA or copying the DLL is unlikely to address an enforced signing policy.

### Safe diagnosis

In the activated project virtual environment, run:

```powershell
python -c "import sys; print(sys.executable); print(sys._base_executable)"
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
python check_setup.py --model
```

If even `import torch` fails with `WinError 4551`, the dashboard can still open but new inference cannot run. Use an interpreter and PyTorch distribution allowed by the machine's policy, or ask the device administrator to review the signed-module policy and Code Integrity logs. An approved Python installation from python.org may help in some configurations but is **not** a guaranteed solution when enterprise policy enforces module signing.

For policy evidence, run this **read-only** command:

```powershell
Get-WinEvent -FilterHashtable @{
  LogName = 'Microsoft-Windows-CodeIntegrity/Operational'
  Id = 3033, 3077
  StartTime = (Get-Date).AddDays(-2)
} -ErrorAction SilentlyContinue |
Where-Object { $_.Message -match 'torch|c10_cuda' } |
Select-Object -First 5 TimeCreated, Id, Message | Format-List
```

## Browser shows a blank processed video

- Open the video file in a desktop player to check it exists.
- The processing script automatically tries to convert OpenCV `mp4v` output to **H.264/yuv420p** using the bundled `imageio-ffmpeg` Python package.
- If H.264 conversion fails, inspect the dashboard warning and verify `python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"`.

## Performance for RTX 3050 6GB

- Begin with 5–15 seconds of one source.
- 4K video is downscaled to a maximum width of 1280 px before model inference.
- Default YOLO inference `imgsz=640`, single frame at a time.
- If CUDA is unavailable but PyTorch imports, uncheck **Use CUDA** and run a short CPU test.
- Do not install/reinstall PyTorch repeatedly in an attempt to bypass Windows signing restrictions.
