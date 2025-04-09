import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Ellipse
import os

from pyowt.OWT import OWT
from pyowt.OpticalVariables import OpticalVariables


# Scatter plot ax limits
AVW_MIN = 430
AVW_MAX = 730
ABC_MIN = -3.6
ABC_MAX = 5
NDI_MIN = -1.0
NDI_MAX = 1.0


def _is_instance_of_OWT(variable):
    return isinstance(variable, OWT)


def _is_instance_of_OpticalVariables(variable):
    return isinstance(variable, OpticalVariables)


class PlotOV:
    """Scatter plot of optical variables, AVW, ABC, and NDI.

    Args:
        owt (OWT): OWT instance
    """

    def __init__(self, owt, show_label=True, abc_ndi=False):

        if not _is_instance_of_OWT(owt):
            raise ValueError(
                "The input 'owt' should be an 'OWT' class to get AVW, ABC, and NDI."
            )

        # copy OWT attributes
        self.owt = owt

        # for background ellipse
        #   from spectral library
        self.mean_OWT = owt.classInfo.mean_OWT
        self.covm_OWT = owt.classInfo.covm_OWT

        #   from name and color code
        self.color_OWT = owt.classInfo.typeColHex
        self.name_OWT = owt.classInfo.typeName

        # add NaN for unclassified inputs
        #   for those type_idx = -1 and type_str = 'NaN'
        #   New element appended for color_OWT and name_OWT
        self.color_OWT.append("#000000")  # black
        self.name_OWT.append("NaN")  # unclassified

        # convert code lists to np.array for indexing
        self.color_OWT = np.array(self.color_OWT)
        self.name_OWT = np.array(self.name_OWT)

        if not hasattr(owt, "ABC"):
            raise ValueError(
                "No attribute 'ABC' found in 'owt'. Please use 'owt.run_classification()' to obtain ABC."
            )

        # copy Optical Variable values for scattering plot
        self.AVW = owt.AVW.flatten()
        self.ABC = owt.ABC.flatten()
        self.NDI = owt.NDI.flatten()

        # copy classification results (type name and index)
        self.type_str = owt.type_str.flatten()
        self.type_idx = owt.type_idx.flatten()
        # type_idx = -1 should be replaced as 10 for correct indexing
        self.type_idx = np.where(self.type_idx == -1, 10, self.type_idx)

        # variables for scatter plotting
        plt_color = self.color_OWT[self.type_idx]
        type_marker = np.full(10, "o")
        type_marker = np.append(type_marker, "x")
        plt_marker = type_marker[self.type_idx]
        unique_markers = np.unique(plt_marker)

        ########
        # Plot #
        ########

        # Create figure with two subplots
        if abc_ndi:
            fig, axs = plt.subplots(1, 3, figsize=(15, 5))
        else:
            fig, axs = plt.subplots(1, 2, figsize=(12, 5))
        # TODO return fig? and plt.show() it ?

        # Panel 1: AVW vs ABC
        ax = axs[0]
        ax.set_xlim(AVW_MIN, AVW_MAX)
        ax.set_ylim(ABC_MIN, ABC_MAX)

        for i in range(len(self.mean_OWT)):
            mean = self.mean_OWT[i, [0, 1]]
            # cov = self.covm_OWT[i, :2, :2]
            cov = self.covm_OWT[:2, :2, i]
            color = self.color_OWT[i]
            type_name = self.name_OWT[i]
            if show_label:
                self.draw_ellipse(ax, mean[0], mean[1], cov, color, f"{type_name}")
            else:
                self.draw_ellipse(ax, mean[0], mean[1], cov, color, "")

        for marker in unique_markers:
            mask = plt_marker == marker
            ax.scatter(
                self.AVW[mask],
                self.ABC[mask],
                color=plt_color[mask],
                marker=marker,
                zorder=5,
            )

        ax.set_xlabel("AVW [nm]")
        ax.set_ylabel(r"$\mathrm{A}_\mathrm{BC}$")

        # Panel 2: AVW vs NDI
        ax = axs[1]
        ax.set_xlim(AVW_MIN, AVW_MAX)
        ax.set_ylim(NDI_MIN, NDI_MAX)

        for i in range(len(self.mean_OWT)):
            mean = self.mean_OWT[i, [0, 2]]
            # cov = self.covm_OWT[i, [0, 2]][:, [0, 2]]
            cov = self.covm_OWT[[0, 2], :][:, [0, 2], i]
            color = self.color_OWT[i]
            type_name = self.name_OWT[i]
            if show_label:
                self.draw_ellipse(ax, mean[0], mean[1], cov, color, f"{type_name}")
            else:
                self.draw_ellipse(ax, mean[0], mean[1], cov, color, "")

        for marker in unique_markers:
            mask = plt_marker == marker
            ax.scatter(
                self.AVW[mask],
                self.NDI[mask],
                color=plt_color[mask],
                marker=marker,
                zorder=5,
            )

        ax.set_xlabel("AVW [nm]")
        ax.set_ylabel("NDI")

        if abc_ndi==True:
            # Panel 3: ABC vs NDI 
            ax = axs[2]
            ax.set_xlim(ABC_MIN, ABC_MAX)
            ax.set_ylim(NDI_MIN, NDI_MAX)

            for i in range(len(self.mean_OWT)):
                mean = self.mean_OWT[i, [1, 2]]
                cov = self.covm_OWT[[1, 2], :][:, [1, 2], i]
                color = self.color_OWT[i]
                type_name = self.name_OWT[i]
                if show_label:
                    self.draw_ellipse(ax, mean[0], mean[1], cov, color, f"{type_name}")
                else:
                    self.draw_ellipse(ax, mean[0], mean[1], cov, color, "")

            for marker in unique_markers:
                mask = plt_marker == marker
                ax.scatter(
                    self.ABC[mask],
                    self.NDI[mask],
                    color=plt_color[mask],
                    marker=marker,
                    zorder=5,
                )

            ax.set_xlabel(r"$\mathrm{A}_\mathrm{BC}$")
            ax.set_ylabel("NDI")

        plt.tight_layout()
        plt.show()

    @staticmethod
    def draw_ellipse(ax, mean_x, mean_y, cov, color, label, n_std=1.0):
        # TODO check why ellipse here is different from that in R...
        # Calculate the eigenvalues and eigenvectors of the covariance matrix
        v, w = np.linalg.eigh(cov)
        order = v.argsort()[::-1]
        v = v[order]
        w = w[:, order]

        angle = np.degrees(np.arctan2(*w[:, 0][::-1]))

        # Width and height are "full" widths, not radius
        width, height = 2 * n_std * np.sqrt(v)
        ellipse = Ellipse(
            xy=(mean_x, mean_y),
            width=width,
            height=height,
            angle=angle,
            edgecolor="#000000",
            facecolor="none",
            label=label,
            zorder=6,
        )

        ax.add_patch(ellipse)
        ax.text(
            mean_x,
            mean_y,
            label,
            fontsize=12,
            color=color,
            bbox=dict(facecolor="white", alpha=0.8, edgecolor="none"),
            ha="center",
            va="center",
            zorder=7,
        )


class PlotSpec:

    def __init__(
        self,
        owt,
        ov,
        norm=False,
        thre_u=None,
        fill_alpha=0.2,
        spec_alpha=0.8,
        figsize=(12, 8),
    ):
        """Plot spectral distribution of OWT classification results

        Args:
            owt (OWT): OWT instance
            ov (OpticalVariables): OpticalVariables instance
            norm (bool, optional): Plot normalized spectrum or not. Defaults to False.
            thre_u (float, optional): If None, input Rrs will be plotted by classified types;
                otherwise, spectra with memberships greater than thre_u will be plotted for each OWT
            fill_alpha (float, optional): Alpha value for the ribbon of upper and lower ranges of OWT means. 
                Default to 0.8
            spec_alpha (float, optional): Alpha value for input Rrs spectra. Default to 0.8.
            figsize (tuple, optional): Figure size for plotting. Default to (12, 8)
        """

        if not _is_instance_of_OWT(owt):
            raise ValueError(
                "The input 'owt' should be an 'OWT' class to get AVW, ABC, and NDI."
            )

        if not _is_instance_of_OpticalVariables(ov):
            raise ValueError(
                "The input 'ov' should be an 'OpticalVariables' class to get Rrs data."
            )

        # copy OWT attributes
        self.owt = owt

        self.version = owt.version
        spec_lib_file = f"data/{self.version}/OWT_mean_spec.csv"

        # for background spectra
        #   from spectral library
        proj_root = os.path.dirname(os.path.abspath(__file__))
        self.spec_lib_file = os.path.join(proj_root, spec_lib_file)
        self.spec_lib = pd.read_csv(self.spec_lib_file)

        #   from name and color code
        self.color_OWT = owt.classInfo.typeColHex
        self.name_OWT = owt.classInfo.typeName

        # add NaN for unclassified inputs
        #   for those type_idx = -1 and type_str = 'NaN'
        #   New element appended for color_OWT and name_OWT
        self.color_OWT.append("#000000")  # black
        self.name_OWT.append("NaN")  # unclassified

        # convert code lists to np.array for indexing
        self.color_OWT = np.array(self.color_OWT)
        self.name_OWT = np.array(self.name_OWT)

        # copy classification results (type name and index)
        self.type_str = owt.type_str.flatten()
        self.type_idx = owt.type_idx.flatten()
        # type_idx = -1 should be replaced as 10 for correct indexing
        self.type_idx = np.where(self.type_idx == -1, 10, self.type_idx)

        # variables for scatter plotting
        plt_color = self.color_OWT[:-1].tolist()
        type_marker = np.full(10, "o")
        type_marker = np.append(type_marker, "x")

        # get Rrs from ov class
        Rrs = ov.Rrs
        self.band = ov.band
        self.Rrs = Rrs.reshape(-1, Rrs.shape[2])
        self.nRrs = self.Rrs / owt.Area

        # get membership from owt class
        self.u = owt.u.reshape(-1, owt.u.shape[2])

        ########
        # Plot #
        ########

        types = self.spec_lib["type"].unique()

        n_rows = 3
        n_cols = 4

        fig, axs = plt.subplots(
            n_rows, n_cols, figsize=figsize, sharex=True, sharey=True
        )

        ax_unclassified = fig.add_subplot(n_rows, n_cols, n_rows * n_cols - 1)

        axs = axs.flatten()

        # Original scale on Rrs [sr^-1]#
        # loop mean and shadow of spectra for each type
        i_owt = 0
        for ax, t, col in zip(axs, types, plt_color):

            subset = self.spec_lib[self.spec_lib["type"] == t]

            if norm:
                ax.plot(subset["wavelen"], subset["m_nRrs"], color=col, alpha=1)
                ax.fill_between(
                    subset["wavelen"],
                    subset["lo_nRrs"],
                    subset["up_nRrs"],
                    color=col,
                    alpha=fill_alpha,
                )
            else:
                ax.plot(subset["wavelen"], subset["m_Rrs"], color=col, alpha=1)
                ax.fill_between(
                    subset["wavelen"],
                    subset["lo_Rrs"],
                    subset["up_Rrs"],
                    color=col,
                    alpha=fill_alpha,
                )

            # only add labels for left and bottom margins
            # if i_owt % n_cols == 0:
            if i_owt == n_cols:
                if norm:
                    ax.set_ylabel(r"Normalized Rrs [$1/\text{nm}^{2}$]")
                else:
                    ax.set_ylabel(r"Rrs [$\text{sr}^{-1}$]")
            
            if i_owt >= ((n_rows - 1) * n_cols):
                ax.set_xlabel("Wavelength [nm]")

            ax.text(
                0.05,
                0.95,
                f"OWT {t}",
                transform=ax.transAxes,
                fontsize=12,
                verticalalignment="top",
                bbox=dict(facecolor="white", alpha=0.5, edgecolor="none"),
            )

            # check if input Rrs corresponds to the current OWT type and plot in the subpanel
            if thre_u is None:
                # plot for types determined by max memebership
                select_ind = np.where(self.type_str == t)[0]
            else:
                # plot for types that are filttered by membership thresholds
                select_ind = np.where(
                    (self.type_idx < 10) & (self.u[:, i_owt] > thre_u)
                )[0]

            if len(select_ind) > 0:
                if norm:
                    ax.plot(
                        self.band,
                        self.nRrs[select_ind].T,
                        color="black",
                        alpha=spec_alpha,
                    )
                else:
                    ax.plot(
                        self.band,
                        self.Rrs[select_ind].T,
                        color="black",
                        alpha=spec_alpha,
                    )

            i_owt += 1

        # delete empty ax
        fig.delaxes(axs[-1])
        fig.delaxes(axs[-2])

        # Plot unclassified Rrs in the last ax without sharing y-axis
        unclassified_ind = np.where(self.type_idx == 10)[0]
        if len(unclassified_ind) > 0:

            if norm:
                ax_unclassified.plot(
                    self.band,
                    self.nRrs[unclassified_ind].T,
                    color="black",
                    alpha=spec_alpha,
                )
            else:
                ax_unclassified.plot(
                    self.band,
                    self.Rrs[unclassified_ind].T,
                    color="black",
                    alpha=spec_alpha,
                )

        # Set labels and title for the unclassified Rrs plot
        ax_unclassified.set_xlabel("Wavelength [nm]")
        ax_unclassified.set_ylabel("")
        ax_unclassified.text(
            0.05,
            0.95,
            "Unclassified",
            transform=ax_unclassified.transAxes,
            fontsize=12,
            verticalalignment="top",
            bbox=dict(facecolor="white", alpha=0.5, edgecolor="none"),
        )

        ax_unclassified.set_xlim(axs[0].get_xlim())
        ax_unclassified.yaxis.set_label_position('right')
        ax_unclassified.yaxis.tick_right()

        plt.tight_layout()
        plt.subplots_adjust(wspace=0.1)

        plt.show()


if __name__ == "__main__":

    """Test 1"""
    AVW_test = np.array([460, 600, 580])
    Area_test = np.array([0.5, 0.4, 0.6])
    NDI_test = np.array([-0.5, 0.2, 0.4])

    owt = OWT(AVW=AVW_test, Area=Area_test, NDI=NDI_test)
    # print(owt.type_str)
    PlotOV(owt)

    """Test 2"""
    # d0 = pd.read_csv("./data/Rrs_demo.csv")
    # d = d0.pivot_table(index="SampleID", columns="wavelen", values="Rrs")
    # owt_train = d0[d0["wavelen"] == 350].sort_values(by="SampleID").type.values

    # # data preparation for `ov` and `owt` classes
    # Rrs = d.values
    # band = d.columns.tolist()

    # # add an unclassified spectrum for testing
    # Rrs = np.append(Rrs, np.repeat(0.5, len(band)).reshape(1, -1), axis=0)

    # # create `ov` class to calculate three optical variables
    # ov = OpticalVariables(Rrs=Rrs, band=band)

    # # create `owt` class to run optical classification
    # owt = OWT(ov.AVW, ov.Area, ov.NDI)

    # PlotSpec(owt, ov, norm=True, thre_u=0.5)
