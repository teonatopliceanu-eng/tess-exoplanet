import numpy as np
import matplotlib.pyplot as plt
from astropy.timeseries import BoxLeastSquares
import lightkurve as lk

#1 Download TESS photometry from MAST
print("Downloading TESS data for HD 209458...")
search = lk.search_lightcurve("HD 209458", mission="TESS")
print(search)

lc_collection = search.download_all()
lc = lc_collection.stitch().normalize().remove_outliers()

#2 Prepare time and flux arrays
time = lc.time.value
flux = lc.flux.value
flux_err = lc.flux_err.value

#3 Box Least Squares periodogram
print("Running BLS periodogram...")
model = BoxLeastSquares(time, flux, dy=flux_err)

periods = np.linspace(1, 5, 10000)   #search 1–5 day periods
result  = model.power(periods, 0.1)  #0.1 day transit duration grid

best_period   = result.period[np.argmax(result.power)]
best_t0       = result.transit_time[np.argmax(result.power)]
best_duration = result.duration[np.argmax(result.power)]

print(f"Best period:   {best_period:.4f} days  (known: ~3.5247 days)")
print(f"Transit epoch: {best_t0:.4f} BTJD")
print(f"Duration:      {best_duration*24:.2f} hours")

#4 Phase-fold the light curve 
phase = ((time - best_t0) % best_period) / best_period
phase[phase > 0.5] -= 1  #centre transit at phase 0

#5 Bin the folded light curve
n_bins  = 100
bins    = np.linspace(-0.5, 0.5, n_bins + 1)
centres = 0.5 * (bins[:-1] + bins[1:])

binned_flux = np.array([
    np.nanmedian(flux[(phase >= bins[i]) & (phase < bins[i+1])])
    for i in range(n_bins)
])

#6 Plot
fig, axes = plt.subplots(2, 1, figsize=(10, 8))

#BLS periodogram
axes[0].plot(result.period, result.power, color="steelblue", lw=0.8)
axes[0].axvline(best_period, color="tomato", ls="--", label=f"P = {best_period:.4f} d")
axes[0].set_xlabel("Period (days)")
axes[0].set_ylabel("BLS Power")
axes[0].set_title("BLS Periodogram — HD 209458")
axes[0].legend()

#Phase-folded light curve
axes[1].scatter(phase, flux, s=1, color="steelblue", alpha=0.3, label="TESS data")
axes[1].plot(centres, binned_flux, color="tomato", lw=2, label="Binned")
axes[1].set_xlabel("Phase")
axes[1].set_ylabel("Normalised Flux")
axes[1].set_title(f"Phase-folded Light Curve  (P = {best_period:.4f} d)")
axes[1].set_xlim(-0.1, 0.1)   #zoom in on transit
axes[1].legend()

plt.tight_layout()
plt.savefig("hd209458_transit.png", dpi=150)
plt.show()
print("Plot saved to hd209458_transit.png")