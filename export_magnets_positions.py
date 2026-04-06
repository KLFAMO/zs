"""
Export magnet positions and rotations to magnets_positions.dat
"""
import numpy as np
from zs_mgp_nofc_v2 import create_zs

# Optimal parameters from the fitted curve
popt = [0, 140, 50, 50, 0, 0,  
        160, 300, 50, 50, 0, 0]

# Create the ZeemanSlower configuration with optimal parameters
sides = ['+y', '-y']
zs = create_zs(*popt, sides=sides)

# Prepare data for export
magnet_data = []
for idx, magnet in enumerate(zs.magnets):
    pos_x, pos_y, pos_z = magnet.position
    rot_x, rot_y, rot_z = magnet.rotation
    
    magnet_data.append({
        'id': idx,
        'pos_x': pos_x,
        'pos_y': pos_y,
        'pos_z': pos_z,
        'rot_x': rot_x,
        'rot_y': rot_y,
        'rot_z': rot_z,
    })

# Export to file with header
header = "ID\tPos_X(mm)\tPos_Y(mm)\tPos_Z(mm)\tRot_X(deg)\tRot_Y(deg)\tRot_Z(deg)"

with open('magnets_positions.dat', 'w') as f:
    f.write(header + '\n')
    for data in magnet_data:
        line = f"{data['id']}\t{data['pos_x']:.6f}\t{data['pos_y']:.6f}\t{data['pos_z']:.6f}\t{data['rot_x']:.6f}\t{data['rot_y']:.6f}\t{data['rot_z']:.6f}\n"
        f.write(line)

print(f"✓ Plik 'magnets_positions.dat' wygenerowany pomyślnie!")
print(f"✓ Liczba magnesów: {len(magnet_data)}")
print(f"\n{'ID':<5} {'Pos_X(mm)':<12} {'Pos_Y(mm)':<12} {'Pos_Z(mm)':<12} {'Rot_X(°)':<12} {'Rot_Y(°)':<12} {'Rot_Z(°)':<12}")
print("="*85)
for data in magnet_data:
    print(f"{data['id']:<5} {data['pos_x']:<12.2f} {data['pos_y']:<12.2f} {data['pos_z']:<12.2f} {data['rot_x']:<12.2f} {data['rot_y']:<12.2f} {data['rot_z']:<12.2f}")
