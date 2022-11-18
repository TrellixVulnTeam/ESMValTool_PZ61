"""Script to download NOAA-CIRES-20CR."""
import logging
import os

from esmvaltool.cmorizers.data.downloaders.wget import WGetDownloader

logger = logging.getLogger(__name__)


def download_dataset(config, dataset, dataset_info, start_date, end_date,
                     overwrite):
    """Download dataset.

    Parameters
    ----------
    config : dict
        ESMValTool's user configuration
    dataset : str
        Name of the dataset
    dataset_info : dict
         Dataset information from the datasets.yml file
    start_date : datetime
        Start of the interval to download
    end_date : datetime
        End of the interval to download
    overwrite : bool
        Overwrite already downloaded files
    """

    downloader = WGetDownloader(
        config=config,
        dataset=dataset,
        dataset_info=dataset_info,
        overwrite=overwrite,
    )

    os.makedirs(downloader.local_folder, exist_ok=True)

    url = "https://downloads.psl.noaa.gov/Datasets/20thC_ReanV2/Monthlies/"

    downloader.download_file(url + "monolevel/cldwtr.eatm.mon.mean.nc", wget_options=[])
    downloader.download_file(url + "monolevel/pr_wtr.eatm.mon.mean.nc", wget_options=[])
    downloader.download_file(url + "pressure/shum.mon.mean.nc", wget_options=[])
    downloader.download_file(url + "gaussian/monolevel/tcdc.eatm.mon.mean.nc", wget_options=[])
    downloader.download_file(url + "gaussian/monolevel/ulwrf.ntat.mon.mean.nc", wget_options=[])
    downloader.download_file(url + "gaussian/monolevel/uswrf.ntat.mon.mean.nc", wget_options=[])
