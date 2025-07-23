# calculator_app.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import rectpack

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

    # Create a mapping from box label (rid) to its color
    color_map = {f"Box {chr(65 + i)}": box['color'] for i, box in enumerate(box_configs)}

    for rect in final_layout:
        color = color_map.get(rect.rid, 'gray')
        ax.add_patch(patches.Rectangle(
            (rect.x, rect.y), rect.width, rect.height,
            facecolor=color, edgecolor='black', lw=1
        ))
        ax.text(rect.x + rect.width/2, rect.y + rect.height/2, rect.rid,
                ha='center', va='center', fontsize=8, color='black')
    return fig

def generate_layout_description(final_layout, box_configs, algo_name, allow_rotation):
    """Formats the layout data into a human-readable text description."""
    if not final_layout:
        return "No layout generated."

    box_stats = {}
    for i, box in enumerate(box_configs):
        label = f"Box {chr(65 + i)}"
        box_stats[label] = {'total': 0, 'S': 0, 'R': 0, 'w': box['w'], 'l': box['l']}

    for rect in final_layout:
        if rect.rid in box_stats:
            stats = box_stats[rect.rid]
            stats['total'] += 1
            # Check if the packed orientation is standard or rotated
            if (rect.width == stats['w'] and rect.height == stats['l']):
                stats['S'] += 1
            else:
                stats['R'] += 1

    summary = f"- **Winning Heuristic:** `{algo_name}`\n"
    summary += f"- **Total Boxes:** {len(final_layout)}\n\n"

    details = "**Box Breakdown:**\n"
    for label, stats in box_stats.items():
        if stats['total'] > 0:
            is_square = stats['w'] == stats['l']
            if allow_rotation and not is_square:
                details += f"- **{label}:** {stats['total']} (Standard: {stats['S']}, Rotated: {stats['R']})\n"
            else:
                details += f"- **{label}:** {stats['total']}\n"

    return summary + details

# --- Initialize Session State ---
if 'boxes' not in st.session_state:
    st.session_state.boxes = [{'w': 320, 'l': 420, 'q': None, 'color': DEFAULT_COLORS[0], 'priority': True}]

# --- UI Functions ---
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

# --- Streamlit User Interface ---
st.set_page_config(layout="wide")
st.title("📦 Advanced Pallet Loading Calculator")

with st.sidebar:
    st.header("Palette Dimensions (mm)")
    palette_w = st.number_input("Palette Width", value=1200, min_value=1)
    palette_l = st.number_input("Palette Length", value=800, min_value=1)
    allow_rotation = st.checkbox("Allow box rotation", value=True)
    
    st.header("Box Types")
    for i, box in enumerate(st.session_state.boxes):
        label = f"Box {chr(65 + i)}"
        with st.expander(label, expanded=True):
            box['priority'] = st.checkbox("Top Priority", value=box.get('priority', False), key=f"p_{i}")
            
            col1, col2 = st.columns(2)
            box['w'] = col1.number_input(f"Width (mm)", value=box['w'], key=f"w_{i}", min_value=1)
            box['l'] = col2.number_input(f"Height (mm)", value=box['l'], key=f"l_{i}", min_value=1)
            
            q_col, clear_q_col = st.columns([3, 1])
            # UI FIX: Use text_input for cleaner look and easier clearing
            q_str = q_col.text_input("Required Quantity", value=box.get('q') or "", placeholder="Unlimited", key=f"q_str_{i}")
            try:
                box['q'] = int(q_str) if q_str else None
            except ValueError:
                box['q'] = None # Ignore non-integer input
            
            # UI FIX: Use 'X' for a compact clear button
            if clear_q_col.button("X", key=f"clear_q_{i}", use_container_width=True):
                box['q'] = None
                st.rerun()

            c_col, del_col = st.columns(2)
            box['color'] = c_col.color_picker("Color", value=box['color'], key=f"c_{i}")
            if len(st.session_state.boxes) > 1:
                 del_col.button("🗑️ Remove", key=f"del_{i}", on_click=remove_box, args=(i,), use_container_width=True)

    st.button("Add New Box Type", on_click=add_box, use_container_width=True)

# --- Calculation ---
if st.button("Calculate Best Layout", type="primary"):
    
    rectangles_to_pack = []
    priority_required_counts = {}
    all_required_counts = {}
    
    # LOGIC FIX: Check for duplicate sizes
    seen_sizes = {}
    duplicate_warning = ""
    for i, box in enumerate(st.session_state.boxes):
        size_tuple = tuple(sorted((box['w'], box['l'])))
        if size_tuple in seen_sizes:
            duplicate_warning = f"Warning: Box {chr(65 + i)} has the same dimensions as Box {chr(65 + seen_sizes[size_tuple])}. Results may be ambiguous."
        else:
            seen_sizes[size_tuple] = i

    # Build list based on priority
    for i, box in enumerate(st.session_state.boxes):
        label = f"Box {chr(65 + i)}"
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
            label = f"Box {chr(65 + i)}"
            if box.get('q'):
                all_required_counts[label] = box['q']
                for _ in range(box['q']):
                    rectangles_to_pack.append((box['w'], box['l'], label))
            else:
                for _ in range(200):
                    rectangles_to_pack.append((box['w'], box['l'], label))

    # --- Heuristic Tournament ---
    pack_algos = [rectpack.MaxRectsBl, rectpack.MaxRectsBssf, rectpack.MaxRectsBaf, rectpack.MaxRectsBlsf]
    sort_algos = [None] 
    
    best_valid_result = {'count': -1, 'packer': None, 'algo': 'None'}

    with st.spinner("Running heuristic tournament..."):
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
                
                is_valid_layout = True
                for label, required in priority_required_counts.items():
                    if packed_counts[label] < required:
                        is_valid_layout = False
                        break
                
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

    # --- Display Results ---
    st.header("Results")
    if duplicate_warning:
        st.warning(duplicate_warning)

    if best_valid_result['count'] == -1:
        st.error("Could not find any layout that satisfies all TOP PRIORITY required quantities.")
    else:
        final_layout = best_valid_result['packer'][0]
        
        final_packed_counts = {label: 0 for label in all_required_counts.keys()}
        for rect in final_layout:
            if rect.rid in final_packed_counts:
                final_packed_counts[rect.rid] += 1
        
        all_packed = True
        for label, required in all_required_counts.items():
            if final_packed_counts[label] < required:
                st.warning(f"Could not fit all required boxes. Only packed {final_packed_counts[label]} of {required} for {label}.")
                all_packed = False
        
        if all_packed and all_required_counts:
             st.success("Successfully packed all required boxes.")

        col1, col2 = st.columns([1, 1.5]) 
        with col1:
            st.subheader("Layout Description")
            description = generate_layout_description(final_layout, st.session_state.boxes, best_valid_result['algo'], allow_rotation)
            st.markdown(description)
        
        with col2:
            st.subheader("Visual Layout")
            fig = create_layout_figure(palette_w, palette_l, final_layout, st.session_state.boxes)
            st.pyplot(fig)
