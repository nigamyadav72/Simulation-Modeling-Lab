import json
import math
import os
from dataclasses import dataclass
from textwrap import dedent
from uuid import uuid4

import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, Preformatted, SimpleDocTemplate, Spacer
from scipy.stats import chisquare


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "submission_ready_reports")
NOTEBOOK_DIR = os.path.join(OUT_DIR, "notebooks")
PLOT_DIR = os.path.join(OUT_DIR, "plots")
PDF_DIR = os.path.join(OUT_DIR, "pdf")

for d in (OUT_DIR, NOTEBOOK_DIR, PLOT_DIR, PDF_DIR):
    os.makedirs(d, exist_ok=True)


@dataclass
class LabContent:
    number: int
    title: str
    theory: str
    equations_md: list[str]
    equations_pdf: list[str]
    simulation_framework: dict[str, str]
    required_topics: list[str]
    required_topic_explanations: dict[str, str]
    code: str
    results: str
    conclusion: str
    plot_path: str



def make_cell(cell_type: str, source: str) -> dict:
    return {
        "cell_type": cell_type,
        "metadata": {"id": uuid4().hex[:8], "language": "python" if cell_type == "code" else "markdown"},
        "source": [line + "\n" for line in source.rstrip("\n").split("\n")],
    }



def write_notebook(
    path: str,
    title: str,
    theory: str,
    equations_md: list[str],
    simulation_framework: dict[str, str],
    topics: list[str],
    topic_explanations: dict[str, str],
    code: str,
    results: str,
    conclusion: str,
) -> None:
    topic_lines = "\n".join([f"{i}. **{t}**" for i, t in enumerate(topics, start=1)])
    explained_topic_lines = "\n\n".join([f"**{i}. {t}**\n{topic_explanations[t]}" for i, t in enumerate(topics, start=1)])
    equations_block = "\n\n".join(equations_md)
    md1 = f"# {title}\n\n## Objective\nSimulate the experiment and interpret the outcome."
    md_framework = (
        "## Simulation and Modelling Framework\n"
        f"**System/Process Model:** {simulation_framework['model']}\n\n"
        f"**Key Assumptions:** {simulation_framework['assumptions']}\n\n"
        f"**Simulation Method:** {simulation_framework['method']}\n\n"
        f"**Validation Strategy:** {simulation_framework['validation']}"
    )
    md2 = (
        "## Theory\n"
        + theory
        + "\n\n## Mathematical Equations\n"
        + equations_block
        + "\n\n## Required Topics\n"
        + topic_lines
        + "\n\n## Brief Explanation of Required Topics\n"
        + explained_topic_lines
        + "\n\n## How to Run\nExecute the code cell to generate results and graph."
    )
    md3 = f"## Expected Result and Conclusion\n\n{results}\n\n**Conclusion:** {conclusion}"

    notebook = {
        "cells": [
            make_cell("markdown", md1),
            make_cell("markdown", md_framework),
            make_cell("markdown", md2),
            make_cell("code", code),
            make_cell("markdown", md3),
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=2)



def build_pdf(lab: LabContent) -> None:
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        spaceAfter=8,
    )
    heading = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        spaceAfter=6,
    )
    topic_heading = ParagraphStyle(
        "TopicHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        spaceAfter=2,
    )
    equation_style = ParagraphStyle(
        "Equation",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=10,
        leading=13,
        leftIndent=14,
        spaceAfter=5,
    )

    pdf_path = os.path.join(PDF_DIR, f"Lab_{lab.number}_Report.pdf")
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )

    story = []
    story.append(Paragraph(f"Lab {lab.number}: {lab.title}", styles["Title"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("1. Title", heading))
    story.append(Paragraph(lab.title, body))

    story.append(Paragraph("2. Theory", heading))
    story.append(Paragraph(lab.theory.replace("\n", "<br/>"), body))

    story.append(Paragraph("3. Simulation and Modelling Framework", heading))
    story.append(Paragraph(f"<b>System/Process Model:</b> {lab.simulation_framework['model']}", body))
    story.append(Paragraph(f"<b>Key Assumptions:</b> {lab.simulation_framework['assumptions']}", body))
    story.append(Paragraph(f"<b>Simulation Method:</b> {lab.simulation_framework['method']}", body))
    story.append(Paragraph(f"<b>Validation Strategy:</b> {lab.simulation_framework['validation']}", body))

    story.append(Paragraph("4. Mathematical Equations", heading))
    for eq in lab.equations_pdf:
        story.append(Paragraph(eq, equation_style))

    story.append(Paragraph("5. Required Topics", heading))
    for i, topic in enumerate(lab.required_topics, start=1):
        story.append(Paragraph(f"{i}. {topic}", body))

    story.append(Paragraph("6. Brief Explanation of Required Topics", heading))
    for i, topic in enumerate(lab.required_topics, start=1):
        explanation = lab.required_topic_explanations[topic]
        story.append(Paragraph(f"{i}. {topic}", topic_heading))
        story.append(Paragraph(explanation, body))

    story.append(Paragraph("7. Program Code", heading))
    story.append(
        Preformatted(
            lab.code.strip("\n"),
            ParagraphStyle(
                "Code",
                fontName="Courier",
                fontSize=8.3,
                leading=10,
                leftIndent=6,
            ),
        )
    )

    story.append(Paragraph("8. Result", heading))
    story.append(Paragraph(lab.results.replace("\n", "<br/>"), body))

    if os.path.exists(lab.plot_path):
        story.append(Spacer(1, 6))
        story.append(Image(lab.plot_path, width=15.5 * cm, height=8.5 * cm))

    story.append(Paragraph("9. Conclusion", heading))
    story.append(Paragraph(lab.conclusion, body))

    doc.build(story)



def lab1() -> LabContent:
    title = "Simulation of a Spring-Mass System"
    theory = dedent(
        """
        A spring-mass system without damping is modeled by a second-order differential equation.
        The motion is simple harmonic, so displacement oscillates around equilibrium.
        Its natural frequency and time period are obtained from the model parameters.
        In simulation, the equation is solved numerically and compared with theoretical expectations.
        """
    ).strip()
    equations_md = [
        "$$m\\frac{d^2x}{dt^2} + kx = 0$$",
        "$$\\omega = \\sqrt{\\frac{k}{m}}, \\qquad T = 2\\pi\\sqrt{\\frac{m}{k}}$$",
    ]
    equations_pdf = [
        "(1) m(d<super>2</super>x/dt<super>2</super>) + kx = 0",
        "(2) omega = sqrt(k/m),    T = 2pi*sqrt(m/k)",
    ]
    simulation_framework = {
        "model": "Deterministic continuous-time dynamic model of a second-order spring-mass system.",
        "assumptions": "No damping, linear spring force, constant mass, no external forcing.",
        "method": "Numerical ODE simulation using initial conditions over a discrete time grid.",
        "validation": "Compare oscillatory behavior and period against analytical SHM relations.",
    }
    topics = [
        "Ordinary differential equations",
        "Simple harmonic motion",
        "Numerical integration",
        "Displacement-time graph interpretation",
    ]
    topic_explanations = {
        "Ordinary differential equations": "The motion law of the spring-mass system is an ODE, so this topic helps convert physics equations into solvable mathematical form.",
        "Simple harmonic motion": "This gives the expected oscillatory behavior (period, amplitude, equilibrium) used to validate the simulation.",
        "Numerical integration": "Simulation computes approximate solutions at many time points when analytical solutions are not directly used.",
        "Displacement-time graph interpretation": "The graph is the core simulation output and shows whether the model behaves physically correctly.",
    }

    code = dedent(
        """
        import numpy as np
        import matplotlib.pyplot as plt
        from scipy.integrate import solve_ivp

        m = 1.0
        k = 4.0
        x0 = 0.1
        v0 = 0.0

        def model(t, y):
            x, v = y
            dxdt = v
            dvdt = -(k / m) * x
            return [dxdt, dvdt]

        t_eval = np.linspace(0, 20, 1000)
        sol = solve_ivp(model, [0, 20], [x0, v0], t_eval=t_eval)

        x = sol.y[0]
        t = sol.t
        T_theory = 2 * np.pi * np.sqrt(m / k)

        print(f"Theoretical Period (s): {T_theory:.4f}")
        print(f"Max displacement (m): {np.max(x):.4f}")
        print(f"Min displacement (m): {np.min(x):.4f}")

        plt.figure(figsize=(8,4))
        plt.plot(t, x, color='navy')
        plt.title('Spring-Mass Displacement vs Time')
        plt.xlabel('Time (s)')
        plt.ylabel('Displacement x (m)')
        plt.grid(True)
        plt.show()
        """
    ).strip()

    m = 1.0
    k = 4.0
    x0 = 0.1
    v0 = 0.0

    def model(t, y):
        x, v = y
        return [v, -(k / m) * x]

    t_eval = np.linspace(0, 20, 1000)
    from scipy.integrate import solve_ivp

    sol = solve_ivp(model, [0, 20], [x0, v0], t_eval=t_eval)
    x = sol.y[0]

    fig_path = os.path.join(PLOT_DIR, "lab1_spring_mass.png")
    plt.figure(figsize=(8, 4))
    plt.plot(sol.t, x, color="navy")
    plt.title("Spring-Mass Displacement vs Time")
    plt.xlabel("Time (s)")
    plt.ylabel("Displacement x (m)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(fig_path, dpi=180)
    plt.close()

    T_theory = 2 * math.pi * math.sqrt(m / k)
    results = (
        f"Using m = {m} kg, k = {k} N/m, x0 = {x0} m and v0 = {v0} m/s, the displacement oscillates "
        f"periodically around zero. The theoretical period is {T_theory:.4f} s. "
        f"Numerically observed displacement remained between {x.min():.4f} m and {x.max():.4f} m."
    )
    conclusion = "The simulated spring-mass system behaves as simple harmonic motion, validating the theoretical model."

    return LabContent(1, title, theory, equations_md, equations_pdf, simulation_framework, topics, topic_explanations, code, results, conclusion, fig_path)



def lab2() -> LabContent:
    title = "Approximation of Pi Using Monte Carlo Simulation"
    theory = dedent(
        """
        Monte Carlo simulation estimates unknown values by repeated random sampling.
        To approximate pi, random points are generated inside a unit square.
        The ratio of points inside a quarter-circle to the total points estimates the area ratio.
        Multiplying that ratio by 4 gives an approximation of pi.
        """
    ).strip()
    equations_md = [
        "$$x_i, y_i \\sim U(0,1)$$",
        "$$I_i = \\begin{cases}1, & x_i^2 + y_i^2 \\le 1 \\\\ 0, & \\text{otherwise}\\end{cases}$$",
        "$$\\hat{\\pi} = 4\\left(\\frac{1}{N}\\sum_{i=1}^{N} I_i\\right)$$",
    ]
    equations_pdf = [
        "(1) x_i, y_i are uniformly random in [0,1]",
        "(2) Indicator I_i = 1 if x_i^2 + y_i^2 <= 1, else 0",
        "(3) pi_hat = 4 * (sum(I_i)/N)",
    ]
    simulation_framework = {
        "model": "Stochastic geometric probability model using random sampling in a unit square.",
        "assumptions": "Independent and uniformly distributed random points; large sample approximates true area ratio.",
        "method": "Monte Carlo simulation with indicator counting for quarter-circle membership.",
        "validation": "Measure absolute error between estimated pi and reference pi; observe convergence with high N.",
    }
    topics = [
        "Random number generation",
        "Geometric probability",
        "Monte Carlo method",
        "Error analysis",
    ]
    topic_explanations = {
        "Random number generation": "Monte Carlo simulation depends on random samples, so quality random numbers are essential.",
        "Geometric probability": "Pi is estimated from the geometry of points inside and outside a quarter circle.",
        "Monte Carlo method": "This is the simulation framework where repeated random trials approximate a mathematical constant.",
        "Error analysis": "Comparing estimate with true pi quantifies simulation accuracy and convergence quality.",
    }

    code = dedent(
        """
        import numpy as np
        import matplotlib.pyplot as plt

        np.random.seed(42)
        N = 100000
        x = np.random.rand(N)
        y = np.random.rand(N)

        inside = (x**2 + y**2) <= 1
        pi_est = 4 * np.mean(inside)
        abs_error = abs(np.pi - pi_est)

        print(f"Estimated pi: {pi_est:.6f}")
        print(f"Absolute error: {abs_error:.6f}")

        sample = 3000
        plt.figure(figsize=(6,6))
        plt.scatter(x[:sample][inside[:sample]], y[:sample][inside[:sample]], s=3, c='green', label='Inside')
        plt.scatter(x[:sample][~inside[:sample]], y[:sample][~inside[:sample]], s=3, c='crimson', label='Outside')
        plt.title('Monte Carlo Estimation of Pi (Sample View)')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.legend()
        plt.axis('equal')
        plt.grid(True)
        plt.show()
        """
    ).strip()

    np.random.seed(42)
    N = 100000
    x = np.random.rand(N)
    y = np.random.rand(N)
    inside = (x**2 + y**2) <= 1
    pi_est = 4 * np.mean(inside)
    abs_error = abs(math.pi - pi_est)

    fig_path = os.path.join(PLOT_DIR, "lab2_monte_carlo_pi.png")
    sample = 3000
    plt.figure(figsize=(6, 6))
    plt.scatter(x[:sample][inside[:sample]], y[:sample][inside[:sample]], s=3, c="green", label="Inside")
    plt.scatter(x[:sample][~inside[:sample]], y[:sample][~inside[:sample]], s=3, c="crimson", label="Outside")
    plt.title("Monte Carlo Estimation of Pi (Sample View)")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.legend()
    plt.axis("equal")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(fig_path, dpi=180)
    plt.close()

    results = f"For N = {N} random points, the estimated value of pi is {pi_est:.6f}. The absolute error is {abs_error:.6f}."
    conclusion = "The Monte Carlo estimate converges near pi, and increasing sample size improves accuracy."

    return LabContent(2, title, theory, equations_md, equations_pdf, simulation_framework, topics, topic_explanations, code, results, conclusion, fig_path)



def lab3() -> LabContent:
    title = "Simulation of Discharging of a Capacitor"
    theory = dedent(
        """
        In an RC circuit, capacitor voltage decreases exponentially during discharge.
        The time constant is represented by the symbol τ and controls how quickly the voltage drops.
        At time t = τ, the voltage becomes about 36.8% of the initial value.
        This simulation verifies the analytical discharge model through numerical plotting.
        """
    ).strip()
    equations_md = [
        "$$V(t) = V_0 e^{-t/(RC)}$$",
        "$$\\tau = RC$$",
        "$$V(\\tau) = V_0 e^{-1} \\approx 0.368V_0$$",
    ]
    equations_pdf = [
        "(1) V(t) = V0 * exp(-t/(RC))",
        "(2) tau symbol: τ = RC",
        "(3) At t = τ, V(τ) = V0/e ≈ 0.368V0",
    ]
    simulation_framework = {
        "model": "Deterministic first-order RC discharge model with exponential decay.",
        "assumptions": "Ideal resistor and capacitor, no source during discharge, constant R and C values.",
        "method": "Time-domain simulation by evaluating analytical decay equation over sampled times.",
        "validation": "Check simulated voltage at t = τ against theoretical value 0.368V0.",
    }
    topics = [
        "RC circuits",
        "Exponential decay",
        "Time constant concept",
        "Scientific plotting",
    ]
    topic_explanations = {
        "RC circuits": "The capacitor discharge model directly comes from RC circuit behavior.",
        "Exponential decay": "Voltage reduction over time follows an exponential curve, which the simulation must reproduce.",
        "Time constant concept": "The value τ = RC gives a physical timescale for how fast discharge occurs.",
        "Scientific plotting": "A clear voltage-time plot is needed to verify model behavior and present results in reports.",
    }

    code = dedent(
        """
        import numpy as np
        import matplotlib.pyplot as plt

        R = 1000.0      # ohm
        C = 100e-6      # farad
        V0 = 10.0       # volt

        tau = R * C
        t = np.linspace(0, 1.0, 500)
        V = V0 * np.exp(-t / tau)

        print(f"Time constant τ = RC: {tau:.4f} s")
        print(f"Voltage at t=τ: {V0*np.exp(-1):.4f} V")

        plt.figure(figsize=(8,4))
        plt.plot(t, V, color='darkorange')
        plt.axvline(tau, linestyle='--', color='gray', label='τ = RC')
        plt.title('Capacitor Discharging Curve')
        plt.xlabel('Time (s)')
        plt.ylabel('Voltage (V)')
        plt.grid(True)
        plt.legend()
        plt.show()
        """
    ).strip()

    R = 1000.0
    C = 100e-6
    V0 = 10.0
    tau = R * C
    t = np.linspace(0, 1.0, 500)
    V = V0 * np.exp(-t / tau)

    fig_path = os.path.join(PLOT_DIR, "lab3_capacitor_discharge.png")
    plt.figure(figsize=(8, 4))
    plt.plot(t, V, color="darkorange")
    plt.axvline(tau, linestyle="--", color="gray", label="τ = RC")
    plt.title("Capacitor Discharging Curve")
    plt.xlabel("Time (s)")
    plt.ylabel("Voltage (V)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_path, dpi=180)
    plt.close()

    V_tau = V0 * math.exp(-1)
    results = f"For R = {R:.0f} ohm, C = {C:.6f} F and V0 = {V0:.2f} V, τ = {tau:.4f} s. Voltage at t=τ is {V_tau:.4f} V."
    conclusion = "The voltage decays exponentially and matches the theoretical RC discharge equation."

    return LabContent(3, title, theory, equations_md, equations_pdf, simulation_framework, topics, topic_explanations, code, results, conclusion, fig_path)



def lab4() -> LabContent:
    title = "Simulation of Drunk Man Random Walk"
    theory = dedent(
        """
        A drunk man random walk is a stochastic process where each step direction is random.
        In a 2D walk, each step can move up, down, left, or right with equal probability.
        Although the expected displacement is near zero, expected distance from origin grows with sqrt(n).
        """
    ).strip()
    equations_md = [
        "$$\\vec{r}_n = \\sum_{i=1}^{n} \\vec{s}_i$$",
        "$$E[\\vec{r}_n] \\approx 0, \\qquad E[|\\vec{r}_n|] \\propto \\sqrt{n}$$",
    ]
    equations_pdf = [
        "(1) Position after n steps: r_n = s_1 + s_2 + ... + s_n",
        "(2) Expected displacement ~ 0, mean distance from origin grows with sqrt(n)",
    ]
    simulation_framework = {
        "model": "Discrete-time stochastic random walk model on a 2D lattice.",
        "assumptions": "Each step is independent with equal probability among four directions.",
        "method": "Single-path trajectory simulation plus multi-trial ensemble statistics.",
        "validation": "Verify near-zero mean displacement trend and sqrt(n)-type distance growth behavior.",
    }
    topics = [
        "Random walk model",
        "Stochastic process",
        "Mean distance from origin",
        "Simulation statistics",
    ]
    topic_explanations = {
        "Random walk model": "This is the mathematical model of the drunk man's step-by-step movement.",
        "Stochastic process": "Each step is random, so the experiment is governed by probability rather than fixed paths.",
        "Mean distance from origin": "A key performance metric showing how far, on average, the walker ends up after many steps.",
        "Simulation statistics": "Multiple trials and summary statistics are needed to draw reliable conclusions from randomness.",
    }

    code = dedent(
        """
        import numpy as np
        import matplotlib.pyplot as plt

        np.random.seed(7)
        n_steps = 1000
        n_trials = 500

        # Single trajectory
        directions = np.random.randint(0, 4, n_steps)
        step_map = np.array([[1,0],[-1,0],[0,1],[0,-1]])
        steps = step_map[directions]
        path = np.vstack(([0,0], np.cumsum(steps, axis=0)))

        # Ensemble statistics
        final_distances = []
        for _ in range(n_trials):
            d = np.random.randint(0, 4, n_steps)
            s = step_map[d]
            final_pos = np.sum(s, axis=0)
            final_distances.append(np.linalg.norm(final_pos))

        print(f"Mean final distance from origin: {np.mean(final_distances):.4f}")
        print(f"Std. dev. of final distance: {np.std(final_distances):.4f}")

        plt.figure(figsize=(6,6))
        plt.plot(path[:,0], path[:,1], color='teal')
        plt.scatter([0], [0], c='red', label='Start')
        plt.title('2D Drunk Man Random Walk (Single Trial)')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.grid(True)
        plt.axis('equal')
        plt.legend()
        plt.show()
        """
    ).strip()

    np.random.seed(7)
    n_steps = 1000
    n_trials = 500
    step_map = np.array([[1, 0], [-1, 0], [0, 1], [0, -1]])

    directions = np.random.randint(0, 4, n_steps)
    steps = step_map[directions]
    path = np.vstack(([0, 0], np.cumsum(steps, axis=0)))

    final_distances = []
    for _ in range(n_trials):
        d = np.random.randint(0, 4, n_steps)
        s = step_map[d]
        final_pos = np.sum(s, axis=0)
        final_distances.append(float(np.linalg.norm(final_pos)))

    mean_dist = float(np.mean(final_distances))
    std_dist = float(np.std(final_distances))

    fig_path = os.path.join(PLOT_DIR, "lab4_drunk_walk.png")
    plt.figure(figsize=(6, 6))
    plt.plot(path[:, 0], path[:, 1], color="teal")
    plt.scatter([0], [0], c="red", label="Start")
    plt.title("2D Drunk Man Random Walk (Single Trial)")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.grid(True)
    plt.axis("equal")
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_path, dpi=180)
    plt.close()

    results = (
        f"With {n_steps} steps and {n_trials} trials, mean final distance from origin is {mean_dist:.4f} and "
        f"standard deviation is {std_dist:.4f}."
    )
    conclusion = "The random walk confirms stochastic behavior and the growth of average distance with step count."

    return LabContent(4, title, theory, equations_md, equations_pdf, simulation_framework, topics, topic_explanations, code, results, conclusion, fig_path)



def lab5() -> LabContent:
    title = "Simulation of Chi-Squared Test"
    theory = dedent(
        """
        The chi-squared goodness-of-fit test compares observed category frequencies with expected frequencies.
        The test statistic measures the overall deviation between observed and expected counts.
        A p-value larger than the significance level indicates that observed data is consistent with the expected model.
        """
    ).strip()
    equations_md = [
        "$$\\chi^2 = \\sum_{i=1}^{k} \\frac{(O_i - E_i)^2}{E_i}$$",
        "$$H_0: O_i \\text{ follows expected distribution}, \\quad H_1: O_i \\text{ does not}$$",
    ]
    equations_pdf = [
        "(1) chi^2 = sum((O_i - E_i)^2 / E_i)",
        "(2) H0: observed follows expected distribution; H1: it does not",
    ]
    simulation_framework = {
        "model": "Statistical simulation/analysis model for categorical frequency comparison.",
        "assumptions": "Independent observations and adequate expected counts in each category.",
        "method": "Compute chi-squared statistic and p-value from observed and expected frequencies.",
        "validation": "Decision consistency based on significance level alpha and interpreted p-value.",
    }
    topics = [
        "Goodness-of-fit testing",
        "Null and alternative hypotheses",
        "Chi-squared statistic",
        "p-value based decision",
    ]
    topic_explanations = {
        "Goodness-of-fit testing": "This checks whether observed simulation/experimental categories match an expected model.",
        "Null and alternative hypotheses": "These define what it means for data to fit or not fit the expected distribution.",
        "Chi-squared statistic": "It quantifies how much observed counts deviate from expected counts.",
        "p-value based decision": "The p-value provides the decision rule used to accept or reject model consistency.",
    }

    code = dedent(
        """
        import numpy as np
        from scipy.stats import chisquare

        observed = np.array([15, 18, 16, 14, 20, 17])   # counts for die faces 1..6
        total = observed.sum()
        expected = np.full(6, total / 6)

        chi2_stat, p_value = chisquare(f_obs=observed, f_exp=expected)
        alpha = 0.05

        print(f"Observed counts: {observed.tolist()}")
        print(f"Expected counts: {expected.tolist()}")
        print(f"Chi-squared statistic: {chi2_stat:.4f}")
        print(f"p-value: {p_value:.4f}")

        if p_value < alpha:
            print("Decision: Reject H0 (distribution differs significantly).")
        else:
            print("Decision: Fail to reject H0 (distribution is consistent with expectation).")
        """
    ).strip()

    observed = np.array([15, 18, 16, 14, 20, 17])
    total = int(observed.sum())
    expected = np.full(6, total / 6)
    chi2_stat, p_value = chisquare(f_obs=observed, f_exp=expected)
    alpha = 0.05
    decision = (
        "Reject H0 (distribution differs significantly from expected)."
        if p_value < alpha
        else "Fail to reject H0 (distribution is consistent with expected)."
    )

    fig_path = os.path.join(PLOT_DIR, "lab5_chi_square.png")
    x = np.arange(1, 7)
    plt.figure(figsize=(8, 4))
    plt.bar(x - 0.15, observed, width=0.3, label="Observed", color="steelblue")
    plt.bar(x + 0.15, expected, width=0.3, label="Expected", color="orange")
    plt.title("Observed vs Expected Frequencies (Die Faces)")
    plt.xlabel("Die Face")
    plt.ylabel("Frequency")
    plt.xticks(x)
    plt.legend()
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(fig_path, dpi=180)
    plt.close()

    results = (
        f"Observed counts = {observed.tolist()} with total {total}. "
        f"Chi-squared statistic = {chi2_stat:.4f}, p-value = {p_value:.4f}. Decision at alpha=0.05: {decision}"
    )
    conclusion = "The chi-squared framework effectively evaluates whether observed categorical data fits the expected model."

    return LabContent(5, title, theory, equations_md, equations_pdf, simulation_framework, topics, topic_explanations, code, results, conclusion, fig_path)



def main() -> None:
    labs = [lab1(), lab2(), lab3(), lab4(), lab5()]

    for lab in labs:
        nb_path = os.path.join(NOTEBOOK_DIR, f"Lab_{lab.number}.ipynb")
        write_notebook(
            nb_path,
            lab.title,
            lab.theory,
            lab.equations_md,
            lab.simulation_framework,
            lab.required_topics,
            lab.required_topic_explanations,
            lab.code,
            lab.results,
            lab.conclusion,
        )
        build_pdf(lab)

    summary_path = os.path.join(OUT_DIR, "README.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("Submission-ready files generated.\n")
        f.write(f"Notebooks: {NOTEBOOK_DIR}\n")
        f.write(f"PDF Reports: {PDF_DIR}\n")
        f.write(f"Plots: {PLOT_DIR}\n")

    print("Generation completed successfully.")
    print(f"Notebooks directory: {NOTEBOOK_DIR}")
    print(f"PDF directory: {PDF_DIR}")


if __name__ == "__main__":
    main()
