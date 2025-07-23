# calculator_app.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import rectpack

# A list of default colors for new box types
DEFAULT_COLORS = ["#FFADAD", "#FFD6A5", "#FDFFB6", "#CAFFBF", "#9BF6FF", "#A0C4FF", "#BDB2FF", "#FFC6FF"]

def create_layout_figure(palette_w, palette_l, final_layout, box_configs):
    """Creates a Matplotlib figure visualizing the packed layout."""
    fig, ax = plt.subplots(1)
    ax.set_xlim(0, palette_w)
    ax.set_ylim(0, palette_l)
    ax.set_aspect('equal', adjustable='box')
    plt.gca().invert_yaxis()
    ax.add_patch(patches.Rectangle((0, 0), palette_w, palette_l, fill=False, edgecolor='black', lw=2))

    # Create a mapping from box dimensions to its color and label
    color_map = {}
    for i, box in enumerate(box_configs):
        label = f"Box {chr(65 + i)}"
        # Standard
        color_map[(box['w'], box['l'])] = {'color': box['color'], 'label': label}
        # Rotated
        color_map[(box['l'], box['w'])] = {'color': box['color'], 'label': label}

    for rect in final_layout:
        box_info = color_map.get((rect.width, rect.height), {'color': 'gray', 'label': '?'})
        
        ax.add_patch(patches.Rectangle(
            (rect.x, rect.y), rect.width, rect.height,
            facecolor=box_info['color'], edgecolor='black', lw=1
        ))
        ax.text(rect.x + rect.width/2, rect.y + rect.height/2, box_info['label'],
                ha='center', va='center', fontsize=8, color='black')
    return fig

def generate_layout_description(final_layout, box_configs, algo_name, allow_rotation):
    """Formats the layout data into a human-readable text description."""
    if not final_layout:
        return "No layout generated."

    # Initialize data structures to hold counts for each box type
    box_stats = {}
    for i, box in enumerate(box_configs):
        label = f"Box {chr(65 + i)}"
        box_stats[label] = {
            'total': 0, 
            'S': 0, 
            'R': 0,
            'w': box['w'], # Store original dimensions for checking rotation
            'l': box['l']
        }

    # Loop through the packed rectangles to populate the stats
    for rect in final_layout:
        for label, stats in box_stats.items():
            is_standard = (rect.width == stats['w'] and rect.height == stats['l'])
            is_rotated = (rect.width == stats['l'] and rect.height == stats['w'])
            
            if is_standard or is_rotated:
                stats['total'] += 1
                if is_standard:
                    stats['S'] += 1
                else: # is_rotated
                    stats['R'] += 1
                break # Move to the next rectangle

    # Build the final description string
    summary = f"- **Winning Heuristic:** `{algo_name}`\n"
    summary += f"- **Total Boxes:** {len(final_layout)}\n\n"

    details = "**Box Breakdown:**\n"
    for label, stats in box_stats.items():
        if stats['total'] > 0:
            is_square = stats['w'] == stats['l']
            # Only show S/R breakdown if rotation is allowed and the box isn't a square
            if allow_rotation and not is_square:
                details += f"- **{label}:** {stats['total']} (Standard: {stats['S']}, Rotated: {stats['R']})\n"
            else:
                details += f"- **{label}:** {stats['total']}\n"

    return summary + details

# --- Initialize Session State ---
if 'boxes' not in st.session_state:
    st.session_state.boxes = [{'w': 320, 'l': 420, 'q': None, 'color': DEFAULT_COLORS[0]}]

# --- UI Functions ---
def add_box():
    next_color_index = len(st.session_state.boxes) % len(DEFAULT_COLORS)
    st.session_state.boxes.append({'w': 100, 'l': 100, 'q': None, 'color': DEFAULT_COLORS[next_color_index]})

def remove_box(index):
    st.session_state.boxes.pop(index)

# --- Streamlit User Interface ---
st.set_page_config(layout="wide")
st.title("📦 Advanced Pallet Loading Calculator")

# --- Inputs ---
with st.sidebar:
    st.header("Palette Dimensions (mm)")
    palette_w = st.number_input("Palette Width", value=1200, min_value=1)
    palette_l = st.number_input("Palette Length", value=800, min_value=1)
    allow_rotation = st.checkbox("Allow box rotation", value=True)
    
    st.header("Box Types")
    for i, box in enumerate(st.session_state.boxes):
        label = f"Box {chr(65 + i)}"
        with st.expander(label, expanded=True):
            col1, col2 = st.columns(2)
            box['w'] = col1.number_input(f"Width (mm)", value=box['w'], key=f"w_{i}", min_value=1)
            box['l'] = col2.number_input(f"Height (mm)", value=box['l'], key=f"l_{i}", min_value=1)
            
            col3, col4, col5 = st.columns([2,1,1])
            box['q'] = col3.number_input("Required Quantity", value=box.get('q'), key=f"q_{i}", min_value=1, placeholder="Unlimited")
            box['color'] = col4.color_picker("Color", value=box['color'], key=f"c_{i}")
            if len(st.session_state.boxes) > 1:
                 col5.button("🗑️", key=f"del_{i}", on_click=remove_box, args=(i,), use_container_width=True)

    st.button("Add New Box Type", on_click=add_box, use_container_width=True)

# --- Calculation ---
if st.button("Calculate Best Layout", type="primary"):
    
    rectangles_to_pack = []
    required_counts = {}
    
    # Prioritize required boxes by adding them to the list first
    for i, box in enumerate(st.session_state.boxes):
        label = f"Box {chr(65 + i)}"
        if box['q'] is not None:
            required_counts[label] = box['q']
            for _ in range(box['q']):
                rectangles_to_pack.append((box['w'], box['l'], label))

    # Add "unlimited" boxes to the end of the list
    for i, box in enumerate(st.session_state.boxes):
        label = f"Box {chr(65 + i)}"
        if box['q'] is None:
            for _ in range(200): 
                rectangles_to_pack.append((box['w'], box['l'], label))

    # --- Heuristic Tournament ---
    pack_algos = [rectpack.MaxRectsBl, rectpack.MaxRectsBssf, rectpack.MaxRectsBaf, rectpack.MaxRectsBlsf]
    sort_algos = [None, rectpack.SORT_AREA, rectpack.SORT_LSIDE, rectpack.SORT_SSIDE]
    
    best_valid_result = {'count': -1, 'packer': None, 'algo': 'None'}

    with st.spinner("Running heuristic tournament..."):
        for pack_algo in pack_algos:
            for sort_algo in sort_algos:
                packer = rectpack.newPacker(sort_algo=sort_algo, pack_algo=pack_algo, rotation=allow_rotation)
                packer.add_bin(palette_w, palette_l)
                for r in rectangles_to_pack:
                    packer.add_rect(*r)
                packer.pack()
                
                # --- NEW VALIDATION GATE ---
                # Check if this layout is valid by counting the packed required boxes.
                packed_required_counts = {label: 0 for label in required_counts.keys()}
                for rect in packer[0]:
                    if rect.rid in packed_required_counts:
                        packed_required_counts[rect.rid] += 1
                
                is_valid_layout = True
                for label, required in required_counts.items():
                    if packed_required_counts[label] < required:
                        is_valid_layout = False
                        break
                
                # If the layout is not valid, discard it and try the next heuristic.
                if not is_valid_layout:
                    continue

                # --- This layout is valid, now check if it's the best one so far ---
                current_count = len(packer[0])
                if current_count > best_valid_result['count']:
                    sort_algo_name = "Prioritized" if sort_algo is None else sort_algo.__name__.replace('SORT_', '')
                    best_valid_result = {
                        'count': current_count,
                        'algo': f"{pack_algo.__name__} / {sort_algo_name}",
                        'packer': packer
                    }

    # --- Display Results ---
    st.header("Results")
    if best_valid_result['count'] == -1:
        st.error("Could not find any layout that satisfies all required quantities.")
    else:
        final_layout = best_valid_result['packer'][0]

        # Final verification message
        all_required_packed = True
        packed_counts = {label: 0 for label in required_counts.keys()}
        for rect in final_layout:
            if rect.rid in packed_counts:
                packed_counts[rect.rid] += 1
        
        for label, required in required_counts.items():
            if packed_counts[label] < required:
                all_required_packed = False # Should not happen due to new logic, but good for safety
        
        if all_required_packed and required_counts:
             st.success("Successfully packed all required boxes.")

        col1, col2 = st.columns([1, 1.5]) # Give more space to the visual
        with col1:
            st.subheader("Layout Description")
            description = generate_layout_description(final_layout, st.session_state.boxes, best_valid_result['algo'], allow_rotation)
            st.markdown(description)
        
        with col2:
            st.subheader("Visual Layout")
            fig = create_layout_figure(palette_w, palette_l, final_layout, st.session_state.boxes)
            st.pyplot(fig)
