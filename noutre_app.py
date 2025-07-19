import streamlit as st
from PIL import Image
import numpy as np
import cv2
import os

# 動画生成関数
def generate_video(grid, path="output/picross_animation.mp4"):
    cell_size = 50
    rows, cols = grid.shape
    frame_rate = 30
    solve_duration = 7
    pause_duration = 3
    total_frames = solve_duration * frame_rate
    pause_frames = pause_duration * frame_rate
    video_size = (cols * cell_size, rows * cell_size)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(path, fourcc, frame_rate, video_size)

    def draw_grid(step):
        img = np.ones((rows * cell_size, cols * cell_size, 3), dtype=np.uint8) * 255
        for i in range(rows):
            for j in range(cols):
                y1, y2 = i * cell_size, (i + 1) * cell_size
                x1, x2 = j * cell_size, (j + 1) * cell_size
                if grid[i][j] == 1 and i * cols + j < step:
                    cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), -1)
                    cv2.putText(img, "■", (x1 + 12, y1 + 35),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
        # 枠線
        for i in range(rows + 1):
            t = 3 if i % 3 == 0 else 1
            cv2.line(img, (0, i * cell_size), (cols * cell_size, i * cell_size), (0, 0, 0), t)
        for j in range(cols + 1):
            t = 3 if j % 3 == 0 else 1
            cv2.line(img, (j * cell_size, 0), (j * cell_size, rows * cell_size), (0, 0, 0), t)
        return img

    total_cells = np.sum(grid)
    step_counter = 0.0
    cells_per_frame = total_cells / total_frames

    for f in range(total_frames):
        step = int(step_counter)
        img = draw_grid(step)
        out.write(img)
        step_counter += cells_per_frame

    final_img = draw_grid(total_cells)
    for _ in range(pause_frames):
        out.write(final_img)

    out.release()


# ========== Streamlit アプリ開始 ==========

st.set_page_config(page_title="ノウトレ", layout="centered")
st.title("🧠 ノウトレ - ピクロス動画ジェネレーター")
st.caption("画像をアップロード → ピクロスに変換 → 解答アニメ動画を自動生成！")

uploaded_file = st.file_uploader("① 画像をアップロードしてください（jpg / png）", type=["jpg", "jpeg", "png"])

if uploaded_file:
    # フォルダ作成
    os.makedirs("output", exist_ok=True)

    # モノクロ変換 → 10x10にリサイズ
    image = Image.open(uploaded_file).convert("L")
    img_array = np.array(image.resize((10, 10)))
    threshold = 128
    binary = (img_array < threshold).astype(int)

    st.write("🧩 ピクロス用のグリッド（10×10）:")
    st.image(binary * 255, caption="変換後グリッド", use_column_width=False, width=200)

    # ヒント生成
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

    row_hints = calc_hints(binary)
    col_hints = calc_hints(binary.T)

    st.write("📌 行ヒント（左→右）:")
    st.write(row_hints)
    st.write("📌 列ヒント（上→下）:")
    st.write(col_hints)

    if st.button("② ピクロス解答動画を生成する（10秒）"):
        with st.spinner("🧠 脳内シミュレーション中…"):
            generate_video(binary)
        st.success("✅ 動画が完成しました！下から再生・保存できます。")

        video_file = open("output/picross_animation.mp4", "rb")
        st.video(video_file.read())
        st.download_button("⬇️ mp4をダウンロード", data=video_file, file_name="picross_animation.mp4")
else:
    st.info("画像をアップすると、ピクロス動画の生成ができます。")
