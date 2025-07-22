import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
import os
from moviepy.editor import ImageSequenceClip
import tempfile

st.set_page_config(page_title="ノウトレ", layout="centered")
st.title("🧠 ノウトレ - ピクロス動画ジェネレーター")
st.caption("画像をアップロード → ピクロスに変換 → 解答アニメ動画を自動生成！")

uploaded_file = st.file_uploader("① 画像をアップロードしてください（jpg / png）", type=["jpg", "jpeg", "png"])

# ヒント計算（3値対応）
def calc_hints(grid, target_value):
    hints = []
    for line in grid:
        hint = []
        count = 0
        for cell in line:
            if cell == target_value:
                count += 1
            elif count > 0:
                hint.append(count)
                count = 0
        if count > 0:
            hint.append(count)
        hints.append(hint or [0])
    return hints

# アニメーション生成（3色対応）
def generate_frames(grid, cell_size=32, duration_sec=10, pause_sec=3):
    rows, cols = grid.shape
    total_cells = np.sum(grid > 0)  # 白以外のセルを数える
    frame_rate = 30
    solve_frames = int(frame_rate * (duration_sec - pause_sec))
    pause_frames = int(frame_rate * pause_sec)
    cells_per_frame = total_cells / solve_frames
    frames = []
    step = 0.0
    current = 0

    for f in range(solve_frames):
        img = Image.new("RGB", (cols * cell_size, rows * cell_size), "white")
        draw = ImageDraw.Draw(img)
        cell_counter = 0
        for i in range(rows):
            for j in range(cols):
                x1, y1 = j * cell_size, i * cell_size
                x2, y2 = x1 + cell_size, y1 + cell_size
                if grid[i][j] > 0 and cell_counter < int(step):
                    color = "gray" if grid[i][j] == 1 else "black"
                    draw.rectangle([x1, y1, x2, y2], fill=color)
                if grid[i][j] > 0:
                    cell_counter += 1
                draw.rectangle([x1, y1, x2, y2], outline="black", width=3 if (i % 3 == 0 or j % 3 == 0) else 1)
        frames.append(img)
        step += cells_per_frame

    for _ in range(pause_frames):
        frames.append(frames[-1])
    return frames

if uploaded_file:
    os.makedirs("output", exist_ok=True)

    image = Image.open(uploaded_file).convert("L")
    img_array = np.array(image.resize((30, 30)))

    st.subheader("② 白黒グレー変換のしきい値（2段階）")
    low = st.slider("暗 → グレー のしきい値", 0, 255, 85)
    high = st.slider("グレー → 黒 のしきい値", 0, 255, 170)

    # 3値化（0: 白, 1: グレー, 2: 黒）
    quantized = np.digitize(img_array, bins=[low, high])

    # 拡大表示用に変換（白=255, グレー=127, 黒=0）
    display_img = np.full_like(quantized, 255)
    display_img[quantized == 1] = 127
    display_img[quantized == 2] = 0
    grid_image = Image.fromarray(display_img.astype(np.uint8)).resize((960, 960), resample=Image.NEAREST)

    st.write("🧩 ピクロスグリッド（30×30／3色）:")
    st.image(grid_image, caption="白＝空白、グレー＝中間、黒＝濃い", use_container_width=False)

# グレーと黒それぞれのヒントを取得
row_hints_gray = calc_hints(quantized, target_value=1)
col_hints_gray = calc_hints(quantized.T, target_value=1)
row_hints_black = calc_hints(quantized, target_value=2)
col_hints_black = calc_hints(quantized.T, target_value=2)

# 並列表示
st.write("📌 行・列ヒント（グレー / 黒）")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 行ヒント")
    for i in range(len(row_hints_gray)):
        gray = row_hints_gray[i]
        black = row_hints_black[i]
        st.markdown(f"行 {i}: <span style='color:#888'>G{gray}</span> / <span style='color:#000'>B{black}</span>", unsafe_allow_html=True)

with col2:
    st.markdown("#### 列ヒント")
    for i in range(len(col_hints_gray)):
        gray = col_hints_gray[i]
        black = col_hints_black[i]
        st.markdown(f"列 {i}: <span style='color:#888'>G{gray}</span> / <span style='color:#000'>B{black}</span>", unsafe_allow_html=True)


    if st.button("③ ピクロス解答動画を生成（10秒）"):
        with st.spinner("🧠 動画生成中…"):
            frames = generate_frames(quantized)
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
