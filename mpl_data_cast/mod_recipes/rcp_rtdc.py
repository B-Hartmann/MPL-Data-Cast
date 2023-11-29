import dclab
import dclab.cli
import hdf5plugin

from ..recipe import Recipe


class RTDCRecipe(Recipe):
    __doc__ = f"""
    Compress DC data and include .ini files (dclab {dclab.__version__})
    """

    def convert_dataset(self, path_list, temp_path, **kwargs):
        """Compress the dataset using dclab and append SoftwareSettings.ini"""
        # first compress the .rtdc file
        dclab.cli.compress(path_out=temp_path, path_in=path_list[0])
        # the rest of the files should be log files
        cmp_kw = hdf5plugin.Zstd(clevel=5)
        if len(path_list) > 1:
            with dclab.RTDCWriter(temp_path, compression_kwargs=cmp_kw) as hw:
                for pp in path_list[1:]:
                    lines = pp.read_text().split("\n")
                    lines = [ll.rstrip() for ll in lines]
                    hw.store_log(pp.name, lines)

    def get_raw_data_iterator(self):
        """Get list of .rtdc files including associated files"""
        for pp in self.path_raw.rglob("*.rtdc"):
            path_list = [pp]
            # search for matching SoftwareSettings.ini files
            if pp.name.startswith("M"):
                pini = pp.with_name(
                    pp.name.split("_")[0] + "_SoftwareSettings.ini")
                if pini.exists():
                    path_list.append(pini)
            yield path_list
