# Cài FFmpeg qua pip trên Windows CMD

Trong CMD, dừng backend bằng Ctrl+C và chạy:

```cmd
python -m pip install imageio-ffmpeg
python -c "import imageio_ffmpeg, shutil; shutil.copy2(imageio_ffmpeg.get_ffmpeg_exe(), 'web/backend/ffmpeg.exe')"
cd web\backend
set "PATH=%CD%;%PATH%"
ffmpeg -version
python -m uvicorn main:app --reload
```

Chạy từ thư mục gốc dự án. Những lần mở CMD sau, vào `web\backend` và chạy `set "PATH=%CD%;%PATH%"` trước khi bật backend. `ffmpeg.exe` ở đây là tệp cục bộ, không đẩy lên GitHub.
