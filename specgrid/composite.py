from collections import OrderedDict
from astropy.units import Quantity

from specgrid import plugins


class ModelStar(object):

    param2model = OrderedDict()

    def __init__(self, models_list):
        self.models_list = models_list
        self.param2model = OrderedDict()
        for model in models_list:
            self.param2model.update(OrderedDict([(param, model)
                                          for param in model.parameters]))
        self.parameters = self.param2model.keys()

    def __getattr__(self, item):
        if item in self.param2model:
            return getattr(self.param2model[item], item)
        else:
            return super(ModelStar, self).__getattribute__(item)

    def __setattr__(self, item, value):
        if item in self.param2model:
            return setattr(self.param2model[item], item, value)
        else:
            super(ModelStar, self).__setattr__(item, value)

    def __call__(self):
        spectrum = self.models_list[0]()
        for model in self.models_list[1:]:
            spectrum = model(spectrum)
        return spectrum
    
    def evaluate(self, **kwargs):
        for kwarg in kwargs:
            current_value = getattr(self, kwarg)
            new_value = kwargs[kwarg]
            if hasattr(current_value, 'unit'):
                new_value = Quantity(new_value, current_value.unit)
            setattr(self, kwarg, new_value)
        return self()

def assemble_model_star(spectral_grid, spectrum=None, normalize_pol=None, plugin_names=[]):

    stellar_physics_plugins = []
    instrument_physics_plugins = []

    for plugin_name in plugin_names:
        if plugin_name in plugins.stellar_physics_plugins:
            current_plugin = plugins.stellar_physics_plugins[plugin_name]
            stellar_physics_plugins.append(current_plugin)

        elif plugin_name in plugins.instrument_physics_plugins:
            current_plugin = plugins.stellar_physics_plugins[plugin_name]

            instrument_physics_plugins.append(current_plugin)

    model_star = ModelStar([spectral_grid] + stellar_physics_plugins
                           + instrument_physics_plugins)

    return model_star

