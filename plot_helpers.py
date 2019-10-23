import matplotlib.pyplot as plt
import seaborn as sns

# Save figs in style suitable for AI manipulation:
def save_figs_for_AI(fig,savefile):
    # Get current date, to add "0418", etc.
    with sns.axes_style("darkgrid"):
        fig.savefig(savefile + ".png")

    with sns.axes_style("white"):
        fig.savefig(savefile + ".pdf")

