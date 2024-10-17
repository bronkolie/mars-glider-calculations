import matplotlib.pyplot as plt
import numpy as np
import csv
import os
import time
import sys

from airfoil import Airfoil

# Given parameters
wing_area = 24.985256859242  # m²
wingspan = 14  # m
oswald_efficiency = 0.85
begin_altitude = 10000  # m
min_velocity = 10  # m/s
max_velocity = 140  # m/s
volume = 11.4  # m³

density = 1550  # kg/m³
# The percentage of the glider's volume that is filled with material
fill_percentage = 1.9
components_mass = 107.12  # kg


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

# Calculated parameters that are constant
mass = (fill_percentage / 100 * density * volume) + 107.12
weight = mass * g  # N
lift = weight  # NScreenshot from 2024-10-17 12-41-45
aspect_ratio = wingspan ** 2 / wing_area

print(f"""Mass: {mass:.3f} kg
Weight: {weight:.3f} N
Aspect Ratio: {aspect_ratio:.3f}""")


# Velocity as X-axis
velocity = np.linspace(start=10, stop=240, num=1000)  # m/s

# The needed lift coefficient depends on the velocity, but not on the airfoil
lift_coefficient = lift / (0.5 * air_density * velocity**2 * wing_area)

# Plotting setup
fig, plots = plt.subplots(nrows=1, ncols=3, figsize=(20, 10))
airfoils.sort(key=lambda x: x.name)

print("Calculating...")
start_time = time.time()

for airfoil in airfoils:
    # Retreive the alpha, Cd and Cl data from the CSV
    airfoil_path = os.path.join("airfoils", airfoil.filename)
    with open(airfoil_path) as airfoil_csv:
        csv_reader = csv.reader(airfoil_csv)

        alphas = []
        cls = []
        cds = []
        for _ in range(11):
            next(csv_reader)
        for row in csv_reader:
            alphas.append(float(row[0]))
            cls.append(float(row[1]))
            cds.append(float(row[2]))

    # Initialize the arrays to NaN incase the graph doesn't exist at that point
    angle_of_attack = [np.nan for _ in range(len(velocity))]
    zero_lift_drag_coefficient = [np.nan for _ in range(len(velocity))]

    for i, needed_cl in enumerate(lift_coefficient):
        # Find the smallest needed alpha for the needed Cl, if it exists
        found_alpha = False
        for j, (alpha, cl) in enumerate(zip(alphas, cls)):
            if cl >= needed_cl and (not found_alpha or alpha < min_alpha):
                min_alpha = alpha
                alpha_index = j
                found_alpha = True

        # If an alpha was not found, the graph doesn't exist at this point
        if not found_alpha:
            continue

        # The smallest value in the dataset above, and the biggest value in the dataset under the needed cl and alpha
        bigger_cl = cls[alpha_index]
        bigger_alpha = alphas[alpha_index]
        smaller_alpha = alphas[alpha_index-1]
        smaller_cl = cls[alpha_index-1]

        # Linearly interpolate alpha between the values in our airfoil data, unless it was the first value
        if alpha_index <= 0:
            angle_of_attack[i] = bigger_alpha
            zero_lift_drag_coefficient[i] = bigger_cd
            continue

        lerp_amount = (needed_cl - smaller_cl) / (bigger_cl - smaller_cl)
        lerp_alpha = smaller_alpha + lerp_amount * \
            (bigger_alpha - smaller_alpha)

        smaller_cd = cds[alpha_index - 1]
        bigger_cd = cds[alpha_index]
        lerp_cd = smaller_cd + lerp_amount * (bigger_cd - smaller_cd)

        angle_of_attack[i] = lerp_alpha
        zero_lift_drag_coefficient[i] = lerp_cd

    # It needs to be an np array for easy calculations
    zero_lift_drag_coefficient = np.array(zero_lift_drag_coefficient)

    # Perform the calculations
    induced_drag_coefficient = lift_coefficient**2 / \
        (np.pi * oswald_efficiency * aspect_ratio)
    total_drag_coefficient = zero_lift_drag_coefficient + induced_drag_coefficient
    lift_drag_ratio = lift_coefficient / total_drag_coefficient
    glide_ratio = lift_drag_ratio
    glide_distance = glide_ratio * begin_altitude  # m
    glide_pythagorean_distance = np.sqrt(
        glide_distance ** 2 + begin_altitude ** 2)  # m
    glide_time = glide_pythagorean_distance / velocity  # s

    # Add the data to our plots
    plots[0].plot(velocity, glide_distance / 1000, label=airfoil.name)
    plots[1].plot(velocity, glide_time / 60, label=airfoil.name)
    plots[2].plot(velocity, glide_ratio, label=airfoil.name)


elapsed_time = time.time() - start_time
print("Done!")
print(f"Took {elapsed_time:.5f}s")

plots[0].set_title("Glide distance vs velocity")
plots[0].set_ylabel("Glide distance (km)")

plots[1].set_title("Glide time vs velocity")
plots[1].set_ylabel("Glide time (min)")

plots[2].set_title("Glide ratio vs velocity")
plots[2].set_ylabel("Glide ratio")

for plot in plots:
    plot.set_xlabel("Velocity (m/s)")
    plot.grid(True)
    plot.legend()

    # Only initially graph the values we want to see
    plot.set_xlim([None, max_velocity])


def on_close(_):
    sys.exit()


# Exit if user closes the graph window
fig.canvas.mpl_connect("close_event", on_close)
plt.show(block=False)
try:
    input("Press enter to continue...")
except KeyboardInterrupt:
    sys.exit()
