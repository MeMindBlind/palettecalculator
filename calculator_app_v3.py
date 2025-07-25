# calculator_app.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import rectpack

# --- Internationalization (i18n) Setup ---
TRANSLATIONS = {
    "En": {
        "title": "Advanced Pallet Loading Calculator",
        "subtitle": "Using the Maximal Rectangles algorithm to find the best layout.",
        "palette_dims": "Palette Dimensions (mm)",
        "palette_w": "Palette Width",
        "palette_l": "Palette Length",
        "allow_rotation": "Allow box rotation",
        "box_types": "Box Types",
        "box_label": "Box",
        "top_priority": "Top Priority",
        "width_mm": "Width (mm)",
        "length_mm": "Length (mm)",
        "req_qty": "Required Quantity",
        "unlimited": "Unlimited",
        "clear": "X",
        "color": "Color",
        "remove": "🗑️ Remove",
        "add_box": "Add New Box Type",
        "calculate": "Calculate Best Layout",
        "spinner": "Running heuristic tournament...",
        "results": "Results",
        "warn_duplicate": "Warning: Box {box1} has the same dimensions as Box {box2}. Results may be ambiguous.",
        "error_priority": "Could not find any layout that satisfies all TOP PRIORITY required quantities.",
        "warn_required": "Could not fit all required boxes. Only packed {packed} of {required} for {label}.",
        "success_packed": "Successfully packed all required boxes.",
        "desc_header": "Layout Description",
        "visual_header": "Visual Layout",
        "winning_heuristic": "Winning Heuristic",
        "total_boxes": "Total Boxes",
        "breakdown_header": "Box Breakdown",
        "standard": "Standard",
        "rotated": "Rotated",
        "placement_header": "Placement List (X, Y are top-left corners)",
        "position": "Position",
        "size": "Size",
    },
    "繁": {
        "title": "高級棧板裝載計算機",
        "subtitle": "使用最大矩形算法尋找最佳佈局。",
        "palette_dims": "棧板尺寸 (mm)",
        "palette_w": "棧板寬度",
        "palette_l": "棧板長度",
        "allow_rotation": "允許箱子旋轉",
        "box_types": "箱子類型",
        "box_label": "箱子",
        "top_priority": "最優先",
        "width_mm": "寬度 (mm)",
        "length_mm": "長度 (mm)",
        "req_qty": "要求數量",
        "unlimited": "無限",
        "clear": "X",
        "color": "顏色",
        "remove": "🗑️ 移除",
        "add_box": "新增箱子類型",
        "calculate": "計算最佳佈局",
        "spinner": "正在運行啟發式算法競賽...",
        "results": "結果",
        "warn_duplicate": "警告：{box1} 與 {box2} 尺寸相同。結果可能不明確。",
        "error_priority": "無法找到滿足所有最優先要求的佈局。",
        "warn_required": "無法裝入所有要求的箱子。對於 {label}，{required} 個中只裝入了 {packed} 個。",
        "success_packed": "成功裝入所有要求的箱子。",
        "desc_header": "佈局說明",
        "visual_header": "視覺化佈局",
        "winning_heuristic": "最佳啟發式算法",
        "total_boxes": "總箱數",
        "breakdown_header": "箱子細目",
        "standard": "標準",
        "rotated": "旋轉",
        "placement_header": "放置清單 (X, Y 為左上角座標)",
        "position": "位置",
        "size": "尺寸",
    },
    "簡": {
        "title": "高级托盘装载计算器",
        "subtitle": "使用最大矩形算法寻找最佳布局。",
        "palette_dims": "托盘尺寸 (mm)",
        "palette_w": "托盘宽度",
        "palette_l": "托盘长度",
        "allow_rotation": "允许箱子旋转",
        "box_types": "箱子类型",
        "box_label": "箱子",
        "top_priority": "最优先",
        "width_mm": "宽度 (mm)",
        "length_mm": "长度 (mm)",
        "req_qty": "要求数量",
        "unlimited": "无限",
        "clear": "X",
        "color": "颜色",
        "remove": "🗑️ 移除",
        "add_box": "新增箱子类型",
        "calculate": "计算最佳布局",
        "spinner": "正在运行启发式算法竞赛...",
        "results": "结果",
        "warn_duplicate": "警告：{box1} 与 {box2} 尺寸相同。结果可能不明确。",
        "error_priority": "无法找到满足所有最优先要求的布局。",
        "warn_required": "无法装入所有要求的箱子。对于 {label}，{required} 个中只装入了 {packed} 个。",
        "success_packed": "成功装入所有要求的箱子。",
        "desc_header": "布局说明",
        "visual_header": "可视化布局",
        "winning_heuristic": "最佳启发式算法",
        "total_boxes": "总箱数",
        "breakdown_header": "箱子细目",
        "standard": "标准",
        "rotated": "旋转",
        "placement_header": "放置清单 (X, Y 为左上角坐标)",
        "position": "位置",
        "size": "尺寸",
    },
}

# A list of default colors for new box types, expanded for more variety
DEFAULT_COLORS = [
    "#FFADAD", "#FFD6A5", "#FDFFB6", "#CAFFBF", "#9BF6FF", "#A0C4FF", "#BDB2FF", "#FFC6FF",
    "#FFC8DD", "#FFD700", "#F0E68C", "#98FB98", "#AFEEEE", "#DDA0DD", "#F5DEB3", "#E6E6FA"
]

def create_layout_figure(palette_w, palette_l, final_layout, box_configs):
    """Creates a Matplotlib figure visualizing the packed layout."""
    fig, ax = plt.subplots(1)
    ax.set_xlim(0, palette_w)
    ax.set_ylim(0, palette_l)
    ax.set_aspect('equal', adjustable='box')
    plt.gca().invert_yaxis()
    ax.add_patch(patches.Rectangle((0, 0), palette_w, palette_l, fill=False, edgecolor='black', lw=2))

    color_map = {f"{t['box_label']} {chr(65 + i)}": box['color'] for i, (box, t) in enumerate(zip(box_configs, [st.session_state.t]*len(box_configs)))}

    for rect in final_layout:
        color = color_map.get(rect['rid'], 'gray')
        ax.add_patch(patches.Rectangle(
            (rect['x'], rect['y']), rect['w'], rect['h'],
            facecolor=color, edgecolor='black', lw=1
        ))
        
        # Add dimension labels on the edges if the box is large enough
        if rect['w'] > palette_w * 0.05:
             ax.text(rect['x'] + rect['w']/2, rect['y'] + rect['h'] + 5, f"{rect['w']}",
                ha='center', va='top', fontsize=7, color='black')
        
        if rect['h'] > palette_l * 0.05:
             ax.text(rect['x'] + rect['w'] + 5, rect['y'] + rect['h']/2, f"{rect['h']}",
                ha='left', va='center', fontsize=7, color='black', rotation=-90)

    return fig

def generate_layout_description(final_layout, box_configs, algo_name, allow_rotation, t):
    """Formats the layout data into a human-readable text description."""
    if not final_layout:
        return "No layout generated."

    box_stats = {}
    for i, box in enumerate(box_configs):
        label = f"{t['box_label']} {chr(65 + i)}"
        box_stats[label] = {'total': 0, 'S': 0, 'R': 0, 'w': box['w'], 'l': box['l']}

    for rect in final_layout:
        if rect['rid'] in box_stats:
            stats = box_stats[rect['rid']]
            stats['total'] += 1
            if (rect['w'] == stats['w'] and rect['h'] == stats['l']):
                stats['S'] += 1
            else:
                stats['R'] += 1

    summary = f"- **{t['winning_heuristic']}:** `{algo_name}`\n"
    summary += f"- **{t['total_boxes']}:** {len(final_layout)}\n\n"

    details = f"**{t['breakdown_header']}:**\n"
    for label, stats in box_stats.items():
        if stats['total'] > 0:
            is_square = stats['w'] == stats['l']
            if allow_rotation and not is_square:
                details += f"- **{label}:** {stats['total']} ({t['standard']}: {stats['S']}, {t['rotated']}: {stats['R']})\n"
            else:
                details += f"- **{label}:** {stats['total']}\n"
    
    details += f"\n**{t['placement_header']}:**\n"
    for i, rect in enumerate(final_layout):
        details += f"- **{rect['rid']}:** {t['position']} `({rect['x']:.1f}, {rect['y']:.1f})`, {t['size']} `({rect['w']} x {rect['h']})`\n"

    return summary + details

# --- Initialize Session State ---
if 'boxes' not in st.session_state:
    st.session_state.boxes = [{'w': 320, 'l': 420, 'q': None, 'color': DEFAULT_COLORS[0], 'priority': True}]
if 'lang' not in st.session_state:
    st.session_state.lang = "En"

# --- UI Functions ---
def set_lang(lang):
    st.session_state.lang = lang

def add_box():
    used_colors = {box['color'] for box in st.session_state.boxes}
    new_color = DEFAULT_COLORS[0]
    for color in DEFAULT_COLORS:
        if color not in used_colors:
            new_color = color
            break
    st.session_state.boxes.append({'w': 100, 'l': 100, 'q': None, 'color': new_color, 'priority': False})

def remove_box(index):
    st.session_state.boxes.pop(index)

def clear_quantity(index):
    st.session_state.boxes[index]['q'] = None
    st.session_state[f"q_str_{index}"] = ""

# --- Streamlit User Interface ---
st.set_page_config(layout="wide")
t = TRANSLATIONS[st.session_state.lang] # Get current language translations

st.title(f"📦 {t['title']}")
st.write(t['subtitle'])

with st.sidebar:
    # Language Selection
    col1, col2, col3 = st.columns(3)
    if col1.button("繁體", use_container_width=True):
        set_lang("繁")
        st.rerun()
    if col2.button("简体", use_container_width=True):
        set_lang("簡")
        st.rerun()
    if col3.button("En", use_container_width=True):
        set_lang("En")
        st.rerun()

    st.header(t['palette_dims'])
    palette_w = st.number_input(t['palette_w'], value=1200, min_value=1)
    palette_l = st.number_input(t['palette_l'], value=800, min_value=1)
    allow_rotation = st.checkbox(t['allow_rotation'], value=True)
    
    st.header(t['box_types'])
    for i, box in enumerate(st.session_state.boxes):
        label = f"{t['box_label']} {chr(65 + i)}"
        with st.expander(label, expanded=True):
            box['priority'] = st.checkbox(t['top_priority'], value=box.get('priority', False), key=f"p_{i}")
            
            c1, c2 = st.columns(2)
            box['w'] = c1.number_input(t['width_mm'], value=box['w'], key=f"w_{i}", min_value=1)
            box['l'] = c2.number_input(t['length_mm'], value=box['l'], key=f"l_{i}", min_value=1)
            
            # --- UI FIX: Use a caption for the label and hide the input's default label ---
            st.caption(t['req_qty'])
            q_col, clear_q_col = st.columns([3, 1])
            q_str = q_col.text_input(
                label=t['req_qty'], # Label is needed for accessibility but hidden
                value=box.get('q') or "", 
                placeholder=t['unlimited'], 
                key=f"q_str_{i}",
                label_visibility="collapsed"
            )
            try:
                box['q'] = int(q_str) if q_str else None
            except (ValueError, TypeError):
                box['q'] = None 
            
            if clear_q_col.button(t['clear'], key=f"clear_q_{i}", use_container_width=True):
                clear_quantity(i)
                st.rerun()

            c_col, del_col = st.columns(2)
            box['color'] = c_col.color_picker(t['color'], value=box['color'], key=f"c_{i}")
            if len(st.session_state.boxes) > 1:
                 del_col.button(t['remove'], key=f"del_{i}", on_click=remove_box, args=(i,), use_container_width=True)

    st.button(t['add_box'], on_click=add_box, use_container_width=True)

# --- Calculation ---
if st.button(t['calculate'], type="primary"):
    
    rectangles_to_pack = []
    priority_required_counts = {}
    all_required_counts = {}
    
    seen_sizes = {}
    duplicate_warning_key = None
    for i, box in enumerate(st.session_state.boxes):
        size_tuple = tuple(sorted((box['w'], box['l'])))
        label = f"{t['box_label']} {chr(65 + i)}"
        if size_tuple in seen_sizes:
            other_label = f"{t['box_label']} {chr(65 + seen_sizes[size_tuple])}"
            duplicate_warning_key = ("warn_duplicate", {'box1': label, 'box2': other_label})
        else:
            seen_sizes[size_tuple] = i

    for i, box in enumerate(st.session_state.boxes):
        label = f"{t['box_label']} {chr(65 + i)}"
        if box.get('priority'):
            if box.get('q'):
                priority_required_counts[label] = box['q']
                all_required_counts[label] = box['q']
                for _ in range(box['q']):
                    rectangles_to_pack.append((box['w'], box['l'], label))
            else:
                for _ in range(200): 
                    rectangles_to_pack.append((box['w'], box['l'], label))

    for i, box in enumerate(st.session_state.boxes):
        if not box.get('priority'):
            label = f"{t['box_label']} {chr(65 + i)}"
            if box.get('q'):
                all_required_counts[label] = box['q']
                for _ in range(box['q']):
                    rectangles_to_pack.append((box['w'], box['l'], label))
            else:
                for _ in range(200):
                    rectangles_to_pack.append((box['w'], box['l'], label))

    pack_algos = [rectpack.MaxRectsBl, rectpack.MaxRectsBssf, rectpack.MaxRectsBaf, rectpack.MaxRectsBlsf]
    sort_algos = [None] 
    
    best_valid_result = {'count': -1, 'packer': None, 'algo': 'None'}

    with st.spinner(t['spinner']):
        for pack_algo in pack_algos:
            for sort_algo in sort_algos:
                packer = rectpack.newPacker(sort_algo=sort_algo, pack_algo=pack_algo, rotation=allow_rotation)
                packer.add_bin(palette_w, palette_l)
                for r in rectangles_to_pack:
                    packer.add_rect(*r)
                packer.pack()
                
                packed_counts = {label: 0 for label in priority_required_counts.keys()}
                for rect in packer[0]:
                    if rect.rid in packed_counts:
                        packed_counts[rect.rid] += 1
                
                is_valid_layout = all(packed_counts.get(label, 0) >= required for label, required in priority_required_counts.items())
                
                if not is_valid_layout:
                    continue

                current_count = len(packer[0])
                if current_count > best_valid_result['count']:
                    sort_algo_name = "Prioritized List" if sort_algo is None else sort_algo.__name__.replace('SORT_', '')
                    best_valid_result = {
                        'count': current_count,
                        'algo': f"{pack_algo.__name__} / {sort_algo_name}",
                        'packer': packer
                    }

    st.header(t['results'])
    if duplicate_warning_key:
        st.warning(t[duplicate_warning_key[0]].format(**duplicate_warning_key[1]))

    if best_valid_result['count'] == -1:
        st.error(t['error_priority'])
    else:
        raw_layout = best_valid_result['packer'][0]
        
        if raw_layout:
            max_x = max(rect.x + rect.width for rect in raw_layout)
            max_y = max(rect.y + rect.height for rect in raw_layout)
            x_offset = (palette_w - max_x) / 2
            y_offset = (palette_l - max_y) / 2
        else:
            x_offset, y_offset = 0, 0

        final_layout = [
            {'x': rect.x + x_offset, 'y': rect.y + y_offset, 'w': rect.width, 'h': rect.height, 'rid': rect.rid}
            for rect in raw_layout
        ]

        final_packed_counts = {label: 0 for label in all_required_counts.keys()}
        for rect in final_layout:
            if rect['rid'] in final_packed_counts:
                final_packed_counts[rect['rid']] += 1
        
        all_packed = True
        for label, required in all_required_counts.items():
            if final_packed_counts[label] < required:
                st.warning(t['warn_required'].format(packed=final_packed_counts[label], required=required, label=label))
                all_packed = False
        
        if all_packed and all_required_counts:
             st.success(t['success_packed'])

        col1, col2 = st.columns([1, 1.5]) 
        with col1:
            st.subheader(t['desc_header'])
            description = generate_layout_description(final_layout, st.session_state.boxes, best_valid_result['algo'], allow_rotation, t)
            st.markdown(description)
        
        with col2:
            st.subheader(t['visual_header'])
            # Pass the translated 'box_label' to the figure function
            st.session_state.t = t 
            fig = create_layout_figure(palette_w, palette_l, final_layout, st.session_state.boxes)
            st.pyplot(fig)
