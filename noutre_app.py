import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
from moviepy.editor import ImageSequenceClip
import tempfile

st.set_page_config(page_title="ノウトレ", layout="centered")
st.title("🧠 ノウトレ - ピクロス動画ジェネレーター")
st.caption("画像をアップロード → ピクロスに変換 → 解答アニメ動画を自動生成！")

uploaded_file = st.file_uploader("① 画像をアップロードしてください（jpg / png）", type=["jpg", "jpeg", "png"])

# ヒント計算
def calc_hints(grid):
    hints = []
    for line in grid:
        hint = []
        count = 0
        for cell in line:
            if cell == 1:
                count += 1
            elif count > 0:
                hint.append(count)
                count = 0
        if count > 0:
            hint.append(count)
        hints.append(hint or [0])
    return hints

# 画像をPillowで1フレームずつ生成
def generate_frames(grid, cell_size=50, duration_sec=10, pause_sec=3):
    rows, cols = grid.shape
    total_cells = np.sum(grid)
    frame_rate = 30
    solve_frames = int(frame_rate * (duration_sec - pause_sec))
    pause_frames = int(frame_rate * pause_sec)
    cells_per_frame = total_cells / solve_frames
    frames = []
    step = 0.0

    for f in range(solve_frames):
        img = Image.new("RGB", (cols * cell_size, rows * cell_size), "white")
        draw = ImageDraw.Draw(img)
        # グリッドを描く
        for i in range(rows):
            for j in range(cols):
                x1, y1 = j * cell_size, i * cell_size
                x2, y2 = x1 + cell_size, y1 + cell_size
                if i * cols + j < int(step) and grid[i][j] == 1:
                    draw.rectangle([x1, y1, x2, y2], fill="blue")
                draw.rectangle([x1, y1, x2, y2], outline="black", width=3 if (i % 3 == 0 or j % 3 == 0) else 1)
        frames.append(img)
        step += cells_per_frame

    # 完成後の静止フレーム
    for _ in range(pause_frames):
        frames.append(frames[-1])

    return frames

if uploaded_file:
    os.makedirs("output", exist_ok=True)

    image = Image.open(uploaded_file).convert("L")
    img_array = np.array(image.resize((10, 10)))
    binary = (img_array < 128).astype(int)

    st.write("🧩 ピクロスグリッド（10×10）:")
    st.image(binary * 255, width=200)

    row_hints = calc_hints(binary)
    col_hints = calc_hints(binary.T)
    st.write("📌 行ヒント:", row_hints)
    st.write("📌 列ヒント:", col_hints)

    if st.button("② ピクロス解答動画を生成（10秒）"):
        with st.spinner("🧠 動画生成中…"):
            frames = generate_frames(binary)
            temp_dir = tempfile.mkdtemp()
            clip = ImageSequenceClip([np.array(f) for f in frames], fps=30)
            output_path = os.path.join(temp_dir, "picross.mp4")
            clip.write_videofile(output_path, codec="libx264", audio=False, verbose=False, logger=None)

        st.success("✅ 動画が完成しました！")
        with open(output_path, "rb") as video_file:
            st.video(video_file.read())
            st.download_button("⬇️ mp4をダウンロード", data=video_file, file_name="picross.mp4")
else:
    st.info("画像をアップすると、ピクロス形式に変換されます。")
