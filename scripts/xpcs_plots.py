#!/usr/bin/env python

import sys
import numpy
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.colors import LogNorm
from matplotlib.ticker import FormatStrFormatter
import pylab
import h5py

def gen_image(dset, basename, cbar=True, log=False):
    if sys.platform == 'darwin':
        matplotlib.use("macOSX")

    figsize = (numpy.array(dset.shape) / 100.0)[::-1]
    fig = plt.figure()
    fig.set_size_inches(figsize)
    if cbar:
        figsize[1] *= 1.1
        plt.title(basename)
    else:
        plt.axes([0, 0, 1, 1])  # Make the plot occupy the whole canvas
        plt.axis('off')
    if log:
        image_filename = basename + '_log.png'
        im = plt.imshow(dset,norm=LogNorm())
    else:
        image_filename = basename + '.png'
        im = plt.imshow(dset)
    if cbar:
        ax = plt.gca()
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        plt.colorbar(im, cax=cax)
    plt.savefig(image_filename, dpi=100)

def plot_pixelSum(xpcs_h5file):
    h5fname = xpcs_h5file.filename
    pixelSum_dset = xpcs_h5file['exchange/pixelSum']
    basename = h5fname.rstrip('.hdf') + '_pixelSum'
    gen_image(pixelSum_dset, basename)
    gen_image(pixelSum_dset, basename, log=True)
    gen_image(pixelSum_dset, basename + '_pre', cbar=False)
    gen_image(pixelSum_dset, basename + '_pre', cbar=False, log=True)

def plot_intensity_vs_time(xpcs_h5file):
    basename = xpcs_h5file.filename.rstrip('.hdf')
    i_vs_t = xpcs_h5file['exchange/frameSum']
    pylab.plot(i_vs_t[0], i_vs_t[1])
    plt.xlabel("Elapsed Time (s)")
    plt.ylabel("Average Intensity (photons/pixel/frame)")
    plt.title(basename)
    plt.savefig(basename + '_frameSum.png')

def plot_intensity_vs_q(xpcs_h5file):
    basename = xpcs_h5file.filename.rstrip('.hdf')
    q = xpcs_h5file['/xpcs/sqlist']
    pmt = xpcs_h5file['/exchange/partition-mean-total']
    pylab.loglog(q[0], pmt[0])
    plt.xlabel("q (A^-1)")
    plt.ylabel("Intensity (photons/pixel/frame)")
    plt.title(basename)
    plt.savefig(basename + '_intensity.png')

def plot_g2_all(xpcs_h5file):
    def sfig(bn, gs, ge):
        fig.suptitle('{} Correlations g2 {:d} to {:d}'.format(bn, gs, ge))
        plt.savefig('{}_g2_corr_{:03d}_{:03d}.png'.format(bn, gs, ge), dpi=100)
    
    basename = xpcs_h5file.filename.rstrip('.hdf')
    exp = xpcs_h5file['/measurement/instrument/detector/exposure_period']
    dt = xpcs_h5file['/exchange/tau'][0]*exp[0][0]
    g2_all = xpcs_h5file['/exchange/norm-0-g2']
    g2_err_all = xpcs_h5file['/exchange/norm-0-stderr']
    dynamicQ = xpcs_h5file['/xpcs/dqlist'][0]
    n_plots = dynamicQ.shape[0]

    g_index = 0
    while g_index < n_plots:
        g_start = g_index
        pylab.clf()
        fig, axs = plt.subplots(nrows=3, ncols=3, constrained_layout=True)
        fig.set_size_inches((10,10))
        for i in range(0, 3): # x, left-right axis
            for j in range(0, 3): # y, top-down axis
                ax = axs[i,j]
                ax.errorbar(dt, g2_all[:, g_index], yerr=g2_err_all[:, g_index],
                                fmt='ko', fillstyle='none', capsize=2, markersize=5)
                ax.set_title('q={:f}'.format(dynamicQ[g_index]))
                plt.yscale('linear')
                plt.xscale('log')
                g_index += 1
                if g_index == n_plots:
                    sfig(basename, g_start, g_index - 1)
                    break
        sfig(basename, g_start, g_index - 1)

if __name__ == '__main__':
    import sys
    h5filename = sys.argv[1]
    print('opening ' + h5filename)
    x_h5_file = h5py.File(h5filename, 'r')
    plot_intensity_vs_time(x_h5_file)
    pylab.clf()
    plot_intensity_vs_q(x_h5_file)
    pylab.clf()
    plot_g2_all(x_h5_file)
    pylab.clf()
    plot_pixelSum(x_h5_file)
