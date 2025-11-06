import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="3D Fuel Cell Virtual Lab", layout="wide")

st.title("3D Hydrogen Fuel Cell — Interactive Virtual Lab 🔋🌐")

st.markdown("""
**Instructions:** Use the sliders to change operating conditions. The 3D view shows a simplified schematic of a PEM hydrogen fuel cell: **Anode (left)**, **Electrolyte / Membrane (middle)**, **Cathode (right)**.  
- Blue spheres flowing in the external wire are *electrons*.
- Red spheres moving through the membrane are *protons (H⁺)*.
- At the cathode oxygen (O₂) combines with H⁺ and electrons to form water (H₂O).  
Click on parts for a brief description; explanations appear in the right panel.  
""")

# ---- Controls ----
st.sidebar.header("Simulation controls")
H2 = st.sidebar.slider("Hydrogen concentration (relative)", 0.1, 2.0, 1.0, 0.1)
O2 = st.sidebar.slider("Oxygen concentration (relative)", 0.1, 2.0, 1.0, 0.1)
Temperature = st.sidebar.slider("Temperature (°C)", 20, 120, 60, 1)
Voltage = st.sidebar.slider("Cell voltage (V)", 0.5, 1.2, 0.8, 0.01)
Pressure = st.sidebar.slider("Pressure (atm)", 0.5, 3.0, 1.0, 0.1)
speed = st.sidebar.slider("Animation speed (particles/sec)", 1, 10, 4, 1)

st.sidebar.markdown("---")
st.sidebar.markdown("**Quick tips:** Increase H₂ and O₂ to increase reaction rate. Increase Temperature (to a point) to increase kinetics.")

# ---- Simple physics model (very simplified, for visualization & teaching) ----
# Reaction rate proxy (arbitrary units)
rate = (H2 * 0.6 + O2 * 0.4) * (1 + (Temperature - 25) / 300) * Pressure
# current proportional to rate and voltage factor (very rough)
current_density = max(0.01, rate * (Voltage / 1.0) * 0.5)
power = current_density * Voltage * 50  # assume area ~50 cm^2 for display

# ---- Build 3D schematic ----
def create_box(x0, x1, y0, y1, z0, z1, color):
    # return vertices for Mesh3d (a rectangular box)
    x = [x0,x1,x1,x0,x0,x1,x1,x0]
    y = [y0,y0,y1,y1,y0,y0,y1,y1]
    z = [z0,z0,z0,z0,z1,z1,z1,z1]
    i = [0,0,0,4,4,4,1,2,5,6,1,5]
    j = [1,2,3,5,6,7,5,6,6,7,4,2]
    k = [2,3,0,6,7,4,2,3,7,4,5,6]
    return dict(x=x, y=y, z=z, i=i, j=j, k=k, color=color, opacity=0.9)

# Boxes: Anode, Membrane, Cathode
anode = create_box(-2.0, -0.5, -0.8, 0.8, -0.5, 0.5, 'lightskyblue')
membrane = create_box(-0.4, 0.4, -0.9, 0.9, -0.5, 0.5, 'white')
cathode = create_box(0.5, 2.0, -0.8, 0.8, -0.5, 0.5, 'lightcoral')

fig = go.Figure()

# Add mesh boxes
fig.add_trace(go.Mesh3d(**anode, name='Anode'))
fig.add_trace(go.Mesh3d(**membrane, name='Membrane (Electrolyte)'))
fig.add_trace(go.Mesh3d(**cathode, name='Cathode'))

# Add labels as scatter3d points
fig.add_trace(go.Scatter3d(x=[-1.25], y=[0], z=[0.7], mode='text', text=['Anode'], textposition='top center'))
fig.add_trace(go.Scatter3d(x=[0.0], y=[0], z=[0.7], mode='text', text=['Electrolyte'], textposition='top center'))
fig.add_trace(go.Scatter3d(x=[1.25], y=[0], z=[0.7], mode='text', text=['Cathode'], textposition='top center'))

# Electron path (external wire) - a semicircle above the cell
theta = np.linspace(-np.pi/2, np.pi/2, 40)
wire_x = 1.2 * np.cos(theta)
wire_y = 1.6 * np.sin(theta) * 0.4
wire_z = np.full_like(theta, 0.9)

fig.add_trace(go.Scatter3d(x=wire_x, y=wire_y, z=wire_z, mode='lines', line=dict(color='gold', width=6), name='External wire'))

# Particles positions (initial)
n_particles = 12
t = np.linspace(0, 1, n_particles, endpoint=False)
# electron positions along wire parameterized by t
def electron_positions(t_vals, speed_factor=1.0):
    # shift based on time & speed
    ph = (t_vals * speed_factor) % 1.0
    idx = (ph * (len(wire_x)-1)).astype(int)
    return wire_x[idx], wire_y[idx], wire_z[idx]

# protons path (through membrane): simple straight line from anode->cathode through membrane
proton_x = np.linspace(-0.4, 0.4, 40)
proton_y = np.zeros_like(proton_x)
proton_z = np.linspace(-0.3, 0.3, 40)

# initial scatter traces for particles
ex, ey, ez = electron_positions(t, speed)
fig.add_trace(go.Scatter3d(x=ex, y=ey, z=ez, mode='markers', marker=dict(size=4, color='blue'), name='Electrons'))

px = np.interp(t, np.linspace(0,1,len(proton_x)), proton_x)
py = np.interp(t, np.linspace(0,1,len(proton_x)), proton_y)
pz = np.interp(t, np.linspace(0,1,len(proton_x)), proton_z)
fig.add_trace(go.Scatter3d(x=px, y=py, z=pz, mode='markers', marker=dict(size=4, color='red'), name='Protons (H+)'))

# Oxygen clouds at cathode (visual only)
ox_x = np.random.normal(1.4, 0.08, 10)
ox_y = np.random.normal(0, 0.3, 10)
ox_z = np.random.normal(0.2, 0.05, 10)
fig.add_trace(go.Scatter3d(x=ox_x, y=ox_y, z=ox_z, mode='markers', marker=dict(size=5, color='green', opacity=0.6), name='Oxygen (O2)'))

# Layout aesthetics
fig.update_layout(scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False)),
                  margin=dict(l=0, r=0, t=40, b=0),
                  showlegend=False,
                  paper_bgcolor='rgba(0,0,0,0)')

# Right-side explanation area
col1, col2 = st.columns([2,1])
with col1:
    chart = st.plotly_chart(fig, use_container_width=True, sharing='streamlit', height=600)
with col2:
    st.header("Explanation & Readouts")
    st.markdown("**Parts:**")
    st.write("- **Anode:** Hydrogen gas is supplied here. H₂ → 2H⁺ + 2e⁻ (electrons go through external circuit).")
    st.write("- **Electrolyte / Membrane:** Conducts protons (H⁺) only; electrons travel through the external wire.")
    st.write("- **Cathode:** Oxygen reacts with H⁺ and electrons to form water (H₂O).")
    st.markdown("---")
    st.subheader("Current & Power (proxy)")
    st.write(f"- Reaction rate (proxy): **{rate:.2f}**")
    st.write(f"- Approx. current density (a.u.): **{current_density:.2f}**")
    st.write(f"- Approx. power (a.u.): **{power:.2f}**")
    st.markdown("---")
    st.subheader("Interactive hints")
    st.write("- Increase H₂ or O₂ to increase reaction rate (more electrons & protons).")
    st.write("- Increase Temperature and Pressure to a point to speed kinetics.")
    st.write("- Voltage slider simulates operating point; lower voltage often yields higher current in real systems (but we've simplified behavior).")
    st.markdown("---")
    st.subheader("Click any part in the 3D view")
    st.write("Clicking a mesh will highlight it; use the controls to study behavior.")

# ---- Animation update loop (simulated by re-drawing with new particle positions) ----
# We'll update particle positions each rerun (Streamlit does not support full continuous animation by default
# without a server-side loop; we emulate motion by jittering particle positions based on a random seed
# and forcing rerun when slider changes).
seed = int((H2 + O2 + Temperature + Voltage + Pressure) * 1000) % 2**31
rng = np.random.RandomState(seed)
# electrons slide faster when reaction rate high
electron_speed = max(1.0, speed * (1 + rate/4.0))
t_shift = (rng.rand() * 0.5)

ex, ey, ez = electron_positions((t + t_shift) % 1.0, speed_factor=electron_speed)
# update traces by constructing a new figure (simple method)
fig2 = fig.data[:]  # shallow copy of traces
# replace electron and proton traces (they are at indices after the meshes & labels & wire)
# find indices by name
names = [tr.name for tr in fig2]
elec_idx = names.index('Electrons')
prot_idx = names.index('Protons (H+)')
oxy_idx = names.index('Oxygen (O2)')

fig2[elec_idx] = go.Scatter3d(x=ex, y=ey, z=ez, mode='markers', marker=dict(size=6, color='blue'), name='Electrons')
px = np.interp(((t + t_shift) % 1.0), np.linspace(0,1,len(proton_x)), proton_x)
py = np.interp(((t + t_shift) % 1.0), np.linspace(0,1,len(proton_x)), proton_y)
pz = np.interp(((t + t_shift) % 1.0), np.linspace(0,1,len(proton_x)), proton_z)
fig2[prot_idx] = go.Scatter3d(x=px, y=py, z=pz, mode='markers', marker=dict(size=6, color='red'), name='Protons (H+)')

fig3 = go.Figure(data=fig2)
fig3.update_layout(scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False)),
                  margin=dict(l=0, r=0, t=40, b=0), paper_bgcolor='rgba(0,0,0,0)')

# re-render updated figure
chart.plotly_chart(fig3, use_container_width=True)
