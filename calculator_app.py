# calculator_app.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import rectpack

def create_layout_figure(palette_w, palette_l, final_layout):
    """Creates a Matplotlib figure visualizing the packed layout."""
    fig, ax = plt.subplots(1)
    ax.set_xlim(0, palette_w)
    ax.set_ylim(0, palette_l)
    ax.set_aspect('equal', adjustable='box')
    plt.gca().invert_yaxis()
    ax.add_patch(patches.Rectangle((0, 0), palette_w, palette_l, fill=False, edgecolor='black', lw=2))

    for box in final_layout:
        color = 'yellow' if box['type'] == 'S' else 'lightgreen'
        rect = patches.Rectangle(
            (box['x'], box['y']), box['w'], box['l'],
            facecolor=color, edgecolor='black', lw=1
        )
        ax.add_patch(rect)
        ax.text(box['x'] + box['w']/2, box['y'] + box['l']/2, box['type'],
                ha='center', va='center', fontsize=8, color='black')
    return fig

def generate_layout_description(final_layout, algo_name):
    """Formats the layout data into a human-readable text description."""
    if not final_layout:
        return "No layout generated."

    s_count = sum(1 for box in final_layout if box['type'] == 'S')
    r_count = sum(1 for box in final_layout if box['type'] == 'R')
    
    summary = (f"- **Winning Heuristic:** `{algo_name}`\n"
               f"- **Total Boxes:** {len(final_layout)} ({s_count} Standard, {r_count} Rotated)\n\n")
    
    details = "**Placement List (X, Y are top-left corners):**\n"
    for i, box in enumerate(final_layout):
        details += f"- **Box {i+1} ({box['type']}):** Position `({box['x']}, {box['y']})`, Size `({box['w']} x {box['l']})`\n"
    return summary + details

# --- Streamlit User Interface ---
st.set_page_config(layout="wide")
st.title("📦 Pallet Loading Calculator")
st.write("Using the Maximal Rectangles algorithm to find the best layout.")

with st.sidebar:
    st.header("Dimensions (mm)")
    palette_w = st.number_input("Palette Width", value=1200, min_value=1)
    palette_l = st.number_input("Palette Length", value=800, min_value=1)
    box_w = st.number_input("Box Width", value=320, min_value=1)
    box_l = st.number_input("Box Length", value=420, min_value=1)

if st.button("Calculate Best Layout", type="primary"):
    
    rectangles_to_pack = []
    # Add a reasonable number of boxes for the heuristics to try packing
    for i in range(100): 
        rectangles_to_pack.append((box_w, box_l))

    # --- Heuristic Tournament using Maximal Rectangles ---
    # These are different strategies for choosing which box to place next
    # Using the correct, valid sorting algorithms from the library
    sort_algos = [rectpack.SORT_AREA, rectpack.SORT_LSIDE, rectpack.SORT_SSIDE, rectpack.SORT_PERI]
    
    # These are different 'flavors' of the Maximal Rectangles algorithm itself
    # They determine where in the available space a box gets placed
    pack_algos = [rectpack.MaxRectsBl, rectpack.MaxRectsBssf, rectpack.MaxRectsBaf, rectpack.MaxRectsBlsf]
    
    best_result = {'count': 0, 'layout': [], 'algo': 'None'}

    with st.spinner("Running Maximal Rectangles algorithm with different heuristics..."):
        for sort_algo in sort_algos:
            for pack_algo in pack_algos:
                
                # Create a packer with the current combination of heuristics
                packer = rectpack.newPacker(
                    sort_algo=sort_algo, 
                    pack_algo=pack_algo,
                    rotation=True # This is crucial
                )
                
                packer.add_bin(palette_w, palette_l)
                for r in rectangles_to_pack:
                    packer.add_rect(*r)
                
                packer.pack()

                # Check if this result is the best so far
                current_count = len(packer[0])
                if current_count > best_result['count']:
                    best_result['count'] = current_count
                    best_result['algo'] = f"{pack_algo.__name__} / {sort_algo.__name__.replace('SORT_', '')}"
                    
                    # Save the winning layout
                    current_layout = []
                    for rect in packer[0]:
                        is_standard = (rect.width == box_w and rect.height == box_l)
                        box_type = 'S' if is_standard else 'R'
                        current_layout.append({
                            'x': rect.x, 'y': rect.y,
                            'w': rect.width, 'l': rect.height,
                            'type': box_type
                        })
                    best_result['layout'] = current_layout

    # --- Display Results ---
    st.header("Results")
    if best_result['count'] == 0:
        st.warning("Could not fit any boxes on the palette.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Layout Description")
            description = generate_layout_description(best_result['layout'], best_result['algo'])
            st.markdown(description)
        with col2:
            st.subheader("Visual Layout")
            fig = create_layout_figure(palette_w, palette_l, best_result['layout'])
            st.pyplot(fig)
