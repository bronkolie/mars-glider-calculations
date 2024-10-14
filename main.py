import matplotlib.pyplot as plt
import numpy as np
import csv
import os
from airfoil import Airfoil
import time


# Given parameters
wingspan = 14  # m
length = 5.40  # m
chord = 2  # m
wing_area = chord * wingspan  # m²
oswald_efficiency = 0.85
mass = 450  # kg
min_velocity = 10  # m/s
max_velocity = 140  # m/s
begin_altitude = 10000  # m
max_lift_coefficient = 1.5

airfoils = [Airfoil("NACA 0012", "xf-n0012-il-50000.csv"),
            Airfoil("NACA 0009", "xf-n0009sm-il-50000.csv"),
            Airfoil("NACA 2414", "xf-n2414-il-50000.csv"),
            Airfoil("NACA 2415", "xf-n2415-il-50000.csv"),
            Airfoil("NACA 6409", "xf-n6409-il-50000.csv"),
            Airfoil("NACA 0006", "xf-naca0006-il-50000.csv"),
            Airfoil("NACA 0008", "xf-naca0008-il-50000.csv"),
            Airfoil("NACA 0010", "xf-naca0010-il-50000.csv"),
            Airfoil("NACA 0012", "xf-naca0012h-sa-50000.csv"),
            Airfoil("NACA 0015", "xf-naca0015-il-50000.csv"),
            ]


# Static parameters
g = 3.73  # m/s²
air_density = 0.02  # kg/m³

# Calculated parameters
weight = mass * g  # N
lift = weight  # N
aspect_ratio = wing_area**2 / chord


# Velocity as X-axis
velocity = np.linspace(10, 240, 1000)  # m/s
lift_coefficient = lift / (0.5 * air_density * velocity**2 * wing_area)

plots = plt.subplots(1, 3, figsize=(20, 10))[1]


airfoils.sort(key=lambda x: x.name)

print("Calculating...")
start_time = time.time()

for airfoil in airfoils:
    # Retreive the alpha, Cd and Cl data from the CSV
    airfoil_path = os.path.join("airfoils", airfoil.filename)
    with open(airfoil_path) as airfoil_csv:
        alphas = []
        cls = []
        cds = []
        for i, row in enumerate(csv.reader(airfoil_csv)):
            if i < 11:
                continue
            alpha = float(row[0])
            cl = float(row[1])
            cd = float(row[2])
            alphas.append(alpha)
            cls.append(cl)
            cds.append(cd)

    angle_of_attack = [None for _ in range(len(velocity))]
    zero_lift_drag_coefficient = [np.nan for _ in range(len(velocity))]
    for i, needed_cl in enumerate(lift_coefficient):
        # Find the smallest needed alpha for the needed Cl, if it exists
        found_alpha = False
        for j, (alpha, cl) in enumerate(zip(alphas, cls)):
            if cl >= needed_cl and (not found_alpha or alpha < min_alpha):
                min_alpha = alpha
                alpha_index = j
                found_alpha = True

        if not found_alpha:
            continue
        bigger_cl = cls[alpha_index]
        bigger_alpha = alphas[alpha_index]

        # Linearly interpolate alpha between the values in our airfoil data, unless it was the first value
        if alpha_index <= 0:
            angle_of_attack[i] = bigger_alpha
            zero_lift_drag_coefficient[i] = bigger_cd
            continue

        smaller_alpha = alphas[alpha_index-1]
        smaller_cl = cls[alpha_index-1]

        lerp_amount = (needed_cl - smaller_cl) / (bigger_cl - smaller_cl)
        lerp_alpha = smaller_alpha + lerp_amount * \
            (bigger_alpha - smaller_alpha)

        smaller_cd = cds[alpha_index - 1]
        bigger_cd = cds[alpha_index]
        lerp_cd = smaller_cd + lerp_amount * (bigger_cd - smaller_cd)

        angle_of_attack[i] = lerp_alpha
        zero_lift_drag_coefficient[i] = lerp_cd

    zero_lift_drag_coefficient = np.array(zero_lift_drag_coefficient)

    induced_drag_coefficient = lift_coefficient**2 / \
        (np.pi * oswald_efficiency * aspect_ratio)
    total_drag_coefficient = zero_lift_drag_coefficient + induced_drag_coefficient
    lift_drag_ratio = lift_coefficient / total_drag_coefficient
    glide_ratio = lift_drag_ratio
    glide_distance = glide_ratio * begin_altitude  # m
    glide_pythagorean_distance = np.sqrt(
        glide_distance ** 2 + begin_altitude ** 2)  # m
    glide_time = glide_pythagorean_distance / velocity  # s

    plots[0].plot(velocity, glide_distance / 1000, label=airfoil.name)
    plots[1].plot(velocity, glide_time / 60, label=airfoil.name)
    plots[2].plot(velocity, angle_of_attack, label=airfoil.name)


elapsed_time = time.time() - start_time
print("Done!")
print(f"Took {elapsed_time:.5f}s")


plots[0].set_title("Glide distance vs velocity")
plots[0].set_ylabel("Glide distance (km)")

plots[1].set_title("Glide time vs velocity")
plots[1].set_ylabel("Glide time (min)")

plots[2].set_title("Angle of attack vs velocity")
plots[2].set_ylabel("Angle of Attack (°)")

for plot in plots:
    plot.set_xlabel("Velocity (m/s)")
    plot.grid(True)
    plot.legend()
    plot.set_xlim([None, max_velocity])
    plot.relim()

plt.show()
