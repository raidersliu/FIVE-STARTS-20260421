import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import math
import io
import os

# ==========================================
# 核心計算邏輯與輔助函數
# ==========================================
def split_and_sum(date_str):
    digits = [int(ch) for ch in date_str if ch.isdigit()]
    total = sum(digits)
    if date_str[0] == '2':
        total += 18
    return digits, total

def reduce_to_single_digit(n):
    while n > 10:
        n = sum(int(d) for d in str(n))
    return n

def get_type_chain(start_type, steps):
    if start_type == 10:
        return [((start_type + i + 1) % 10) + 1 for i in range(steps)]
    else:
        return [((start_type + i - 1) % 10) + 1 for i in range(steps + 1)]

def count_10_components(date_str):
    year = int(date_str[2:4])
    month = int(date_str[4:6])
    day = int(date_str[6:8])
    return sum(1 for val in [year, month, day] if val % 10 == 0)

def sum_mmdd_digits(date_str):
    mmdd = date_str[4:8]
    digits = [int(d) for d in mmdd]
    summ = sum(digits)
    while summ > 10:
        summ = sum(int(d) for d in str(summ))
    return summ

def analyze_date_code(date_str):
    yy = date_str[2:4]
    mm = date_str[4:6]
    dd = date_str[6:8]
    combined_digits = yy + mm + dd
    digit_count = {str(i): 0 for i in range(1, 11)}
    for ch in combined_digits:
        if ch in digit_count:
            digit_count[ch] += 1
    digit_count["10"] = sum(1 for x in [yy, mm, dd] if int(x) % 10 == 0)
    return digit_count

def modify_code(date_str, digit_count):
    yy = int(date_str[2:4])
    mm = int(date_str[4:6])
    dd = int(date_str[6:8])
    aaa = sum([1 for v in [yy, mm, dd] if v == 10])
    digit_count["1"] = str(int(digit_count["1"]) - aaa)
    return digit_count

def calculate_star_type(birthday_str):
    digits, total_sum = split_and_sum(birthday_str)
    simplified = reduce_to_single_digit(total_sum)
    ten_count = count_10_components(birthday_str)
    personality = sum_mmdd_digits(birthday_str)
    result = {
        "生日": birthday_str,
        "原始加總": total_sum,
        "轉換次數": ten_count,
        "類型 Type": simplified,
        "人格 Personality": personality,
        "星型類型變化": get_type_chain(simplified, ten_count),
        "成熟年齡": total_sum,
        "轉變年齡": [total_sum + 10 * i for i in range(1, ten_count + 1)]
    }
    return result, simplified, ten_count

# ==========================================
# 繪圖函數 (修改為回傳記憶體緩衝區)
# ==========================================
def draw_star_with_repeated_numbers(result, typen, digit_count, ten_count):
    # 動態計算畫布寬度：每多一個轉換就加寬 500px
    width = 800 + (ten_count * 500) 
    height = 1000
    
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    # 修正縮排錯誤，並指定使用 MSJH.ttc
    try:
        font = ImageFont.truetype("MSJH.ttc", 12)
        font_center = ImageFont.truetype("MSJH.ttc", 36)
        font_data = ImageFont.truetype("MSJH.ttc", 18)
    except:
        st.warning("⚠️ 找不到字型檔 MSJH.ttc，將使用預設英文字型（中文可能無法顯示）。請記得將字型檔與 app.py 放在同一個資料夾。")
        font = ImageFont.load_default()
        font_center = ImageFont.load_default()
        font_data = ImageFont.load_default()
        
    # 在左上角加上文字分析結果
    zz = 0
    for k, v in result.items():
        draw.text((50, 50 + zz), f"{k}: {v}", fill='black', font=font_data, anchor="lm")
        zz += 30

    numbers_with_counts = [(str(i), int(digit_count[str(i)])) for i in range(1, 11)]

    # 依照轉換次數，迴圈畫出每一個階段的五芒星
    for trans in range(ten_count + 1):
        
        # 每個星星中心點向右間隔 500px
        center = (400 + (trans * 500), height // 2)
        radius_outer = 200
        radius_inner = 80
        label_offset = 45
        layer_spacing = 12

        points = []
        for i in range(5):
            outer_angle = math.radians(90 + i * 72)
            inner_angle = math.radians(90 + i * 72 + 36)
            points.append((center[0] + radius_outer * math.cos(outer_angle),
                           center[1] - radius_outer * math.sin(outer_angle)))
            points.append((center[0] + radius_inner * math.cos(inner_angle),
                           center[1] - radius_inner * math.sin(inner_angle)))

        # 畫星星的線條
        draw.line(points + [points[0]], fill='black', width=5)

        for idx, (px, py) in enumerate(points):
            number, count = numbers_with_counts[idx]
            
            # 控制外圍紅字逆時針旋轉
            shift_idx = (idx - 1 + typen + trans) % 10
            number1, count1 = numbers_with_counts[shift_idx]
         
            # 重複數字用逗號隔開
            static_text = ",".join([number] * count) if count > 0 else " "
            dy_text = f"({','.join([number1] * count1)})" if count1 > 0 else " "

            angle = math.atan2(py - center[1], px - center[0])
            base_x = px + label_offset * math.cos(angle) 
            base_y = py + label_offset * math.sin(angle)
            
            # 畫上數字
            draw.text((base_x, base_y - layer_spacing), dy_text, fill='red', font=font, anchor="mm")
            draw.text((base_x, base_y + layer_spacing), static_text, fill='black', font=font, anchor="mm")

        # 中心當下的 T 型數字
        current_t = (typen + trans - 1) % 10 + 1
        draw.text(center, "T " + str(current_t), fill='green', font=font_center, anchor="mm")

    # 將圖片轉存為 BytesIO (記憶體緩衝區) 以供 Streamlit 網頁顯示
    img_buffer = io.BytesIO()
    img.save(img_buffer, format="PNG")
    img_buffer.seek(0)
    return img_buffer


# ==========================================
# Streamlit 網頁介面 (UI)
# ==========================================
st.set_page_config(page_title="身體自覺五星術分析", layout="wide")

st.title("🌟 身體自覺五星術分析")
st.markdown("輸入您的生日，即可分析五星術類型，並產生對應的星型變化圖示。")

# 建立左右排版
col1, col2 = st.columns([1, 2])

with col1:
    birthday_input = st.text_input("請輸入生日 (格式: YYYYMMDD)", value="20250519", max_chars=8)
    analyze_btn = st.button("執行分析與繪圖", type="primary", use_container_width=True)

if analyze_btn:
    if len(birthday_input) == 8 and birthday_input.isdigit():
        with st.spinner('運算與繪圖中...'):
            # 執行計算
            result, typen, ten_count = calculate_star_type(birthday_input)
            digit_count = analyze_date_code(birthday_input)
            digit_count = modify_code(birthday_input, digit_count)
            
            with col1:
                st.subheader("📊 分析結果")
                for key, value in result.items():
                    st.write(f"**{key}**: {value}")
            
            with col2:
                st.subheader("🖼️ 星型圖示")
                img_buffer = draw_star_with_repeated_numbers(result, typen, digit_count, ten_count)
                
                # 顯示圖片 (自動縮放適應網頁寬度)
                st.image(img_buffer, caption=f"{birthday_input} 的星型變化圖", use_container_width=True)
                
                # 下載按鈕
                st.download_button(
                    label="📥 下載星型圖檔 (PNG)",
                    data=img_buffer,
                    file_name=f"star_diagram_{birthday_input}.png",
                    mime="image/png",
                    use_container_width=True
                )
    else:
        st.error("⚠️ 輸入格式錯誤，請確認您輸入的是 8 位數字 (例如: 20250519)")
