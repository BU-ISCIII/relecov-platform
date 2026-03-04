from django_plotly_dash.finders import DashComponentFinder


class DashComponentFinderNoDuplicates(DashComponentFinder):
    """Drop duplicated dash-renderer build registration to avoid collectstatic warnings."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        duplicate_component = "dash/dash-renderer/build"
        duplicate_prefix = f"dash/component/{duplicate_component}"

        if duplicate_component in self.storages:
            del self.storages[duplicate_component]
        if duplicate_component in self.locations:
            self.locations.remove(duplicate_component)
        self.components.pop(duplicate_prefix, None)
