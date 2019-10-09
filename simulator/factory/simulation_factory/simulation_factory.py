from enum import Enum

from .parameters import AcquisitionProfile,\
                        ArtifactModel,\
                        GradientProfile,\
                        StejskalTannerType,\
                        TensorValuedByTensorType, \
                        TensorValuedByParamsType,\
                        TensorValuedByEigsType
from .handlers import SimulationHandler
from external.qspace_sampler.sampling import multishell


class SimulationFactory:
    """Factory class used to generate Fiberfox configuration components"""

    class CompartmentType(Enum):
        """Compartments available for simulation in Fiberfox"""
        INTRA_AXONAL = "1"
        INTER_AXONAL = "2"
        EXTRA_AXONAL_1 = "3"
        EXTRA_AXONAL_2 = "4"

    class AcquisitionType(Enum):
        """Acquisition types available in Fiberfox. Can be either a basic Stejskal-Tanner
        linear acquisition or a tensor-valued acquisition."""
        STEJSKAL_TANNER = StejskalTannerType
        TENSOR_VALUED_BY_TENSOR = TensorValuedByTensorType
        TENSOR_VALUED_BY_EIGS = TensorValuedByEigsType
        TENSOR_VALUED_BY_PARAMS = TensorValuedByParamsType

    class NoiseType(Enum):
        """Noise types available in fiberfox. This only correspond to whole image noises,
        acquisition artifacts are described by the artifact methods available in the factory"""
        COMPLEX_GAUSSIAN = "gaussian"
        RICIAN = "rician"

    @staticmethod
    def get_simulation_handler(geometry_handler, compartments=None):
        """
        Returns the handler in which all the components must be put in order to generate the
        xml configuration file for Fiberfox.
        :param geometry_handler: the handler used to generate the geometry for the simulation
        :type geometry_handler: GeometryHandler
        :param compartments: a list of compartment models generated by the factory to preload in the handler
        :type compartments: List, optional
        :return: A simulation handler in which to put all the components to simulate
        :rtype: SimulationHandler
        """
        return SimulationHandler(
            geometry_handler.get_resolution(),
            geometry_handler.get_spacing(),
            compartments
        )

    @staticmethod
    def generate_acquisition_profile(
            echo_time,
            repetition_time,
            n_channels,
            dwell_time=1,
            partial_fourier=1,
            signal_scale=100,
            reverse_phase=False,
            inhomogen_time=50,
            axon_radius=0
    ):
        """
        Generate the acquisition profile component used to simulate the acquisition sequence
        :param echo_time: TE of the sequence (milliseconds)
        :type echo_time: int
        :param repetition_time: TR of the sequence (milliseconds)
        :type repetition_time: int
        :param n_channels: Number of coils to simulate
        :type n_channels: int
        :param dwell_time: Time to acquire a sample of the k-space (milliseconds), 1
        :type dwell_time: int, optional
        :param partial_fourier: Partial fourier ratio, 1
        :type partial_fourier: float, optional
        :param signal_scale: Value by which the output signal is raised, 100
        :type signal_scale: int, optional
        :param reverse_phase: Either to acquire AP or PA, False
        :type reverse_phase: bool, optional
        :param inhomogen_time: Gradient inhomogeneity time (milliseconds), 50
        :type inhomogen_time: int, optional
        :param axon_radius: Radius of the axons of the simulated fiber medium, 0 for auto-determination by Fiberfox, 0
        :type axon_radius: float, optional
        :return: An acquisition profile component
        :rtype: AcquisitionProfile
        """
        return AcquisitionProfile(None, None).set_echo(echo_time)\
                                             .set_repetition(repetition_time)\
                                             .set_n_coils(n_channels)\
                                             .set_dwell(dwell_time)\
                                             .set_partial_fourier(partial_fourier)\
                                             .set_scale(signal_scale)\
                                             .set_reverse_phase(reverse_phase)\
                                             .set_inhomogen_time(inhomogen_time)\
                                             .set_axon_radius(axon_radius)

    @staticmethod
    def generate_gradient_vectors(points_per_shell, max_iter=1000):
        """
        Generate an optimally distributed list of gradient vectors on one or more shell
        :param points_per_shell: list of gradients per shell
        :type points_per_shell: list(int)
        :param max_iter: maximum iterations available for the optimisation algorithm
        :type max_iter: int, optional
        :return: A list of gradient vectors
        :rtype: list(list(float))
        """
        weights = multishell.compute_weights(
            len(points_per_shell),
            points_per_shell,
            [[i for i in range(len(points_per_shell))]],
            [1]
        )
        return multishell.optimize(len(points_per_shell), points_per_shell, weights, max_iter).tolist()

    @staticmethod
    def generate_gradient_profile(
            bvals,
            bvecs,
            n_b0=0,
            g_type=AcquisitionType.STEJSKAL_TANNER,
            *g_type_args,
            **g_type_kwargs
    ):
        """
        Generate the gradient profile component used to simulate an acquisition sequence. Encapsulate the
        gradient directions, b-values, b0 volumes and acquisition sequence type (see AcquisitionType enum).
        :param bvals: list of b-values (must be the same length as the gradient vectors list)
        :type bvals: list(float)
        :param bvecs: list of gradient vectors
        :type bvecs: list(list(float))
        :param n_b0: number of b0 volumes to simulate
        :type n_b0: int, optional
        :param g_type: type of sequence to simulate (see AcquisitionType enum)
        :type g_type: AcquisitionType, optional
        :param g_type_args: positional arguments needed to initialize the sequence type (see .parameters.GradientProfile)
        :param g_type_kwargs: named arguments needed to initialize the sequence type (see .parameters.GradientProfile)
        :return: A gradient profile component
        :rtype: GradientProfile
        """
        return GradientProfile(
            [0 for i in range(n_b0)] + bvals,
            [[0, 0, 0] for i in range(n_b0)] + bvecs,
            g_type.value(*g_type_args, **g_type_kwargs)
        )

    @staticmethod
    def generate_artifact_model(*artifact_models):
        """
        Generate the artifact models component from parameters corresponding to artifact models
        generated by the factory.
        :param artifact_models: multiple parameters each corresponding to an artifact model
        :type artifact_models: dict
        :return: An artifact models component
        :rtype: ArtifactModel
        """
        return ArtifactModel(artifact_models)

    @staticmethod
    def generate_noise_model(noise_type, variance):
        """
        Generates a dictionary describing the noise model of the simulated acquisition
        :param noise_type: type of noise to simulate (see NoiseType enum)
        :type noise_type: NoiseType
        :param variance: variance of the noise distribution
        :type variance: float
        :return: A dictionary describing the noise model
        :rtype: dict
        """
        return {"descr": "addnoise", "noisetype": noise_type, "noisevariance": variance, "value": True}

    @staticmethod
    def generate_motion_model(randomize=False, direction_indexes="random", rotation=(0, 0, 0), translation=(0, 0, 0)):
        """
        Generates a dictionary describing the motion artifact model of the simulated acquisition
        :param randomize: switch the movement as linear or random, False
        :type randomize: bool, optional
        :param direction_indexes: either the indexes of the volumes to affect by motion, or "random", "random"
        :type direction_indexes: list(int) or str, optional
        :param rotation: the rotation applied by the motion, (0, 0, 0)
        :type rotation: list(float), optional
        :param translation: the translation applied by the motion, (0, 0, 0)
        :type translation: list(float), optional
        :return: A dictionary describing the motion model
        :rtype: dict
        """
        return {
            "descr": "doAddMotion",
            "randomMotion": randomize,
            "motionvolumes": direction_indexes,
            "rotation0": rotation[0],
            "rotation1": rotation[1],
            "rotation2": rotation[2],
            "translation0": translation[0],
            "translation1": translation[1],
            "translation2": translation[2],
            "value": True
        }

    @staticmethod
    def generate_distortion_model():
        """
        DO NOT USE, STILL NEED TO SEE HOW TO IMPLEMENT
        :return: A dictionary describing the distortion model
        :rtype: dict
        """
        return {"descr": "doAddDistortions", "value": True}

    @staticmethod
    def generate_eddy_current_model(gradient_strength, gradient_tau=70):
        """
        Generates a dictionary describing the eddy current artifact model of the simulated acquisition
        :param gradient_strength: strength of the eddy current field induced (mT/m)
        :type gradient_strength: float
        :param gradient_tau: time constant for the current (millisecond), 70
        :type gradient_tau: int, optional
        :return: A dictionary describing the eddy current model
        :rtype: dict
        """
        return {"descr": "addeddycurrents", "eddyStrength": gradient_strength, "eddyTau": gradient_tau, "value": True}

    @staticmethod
    def generate_ghosting_model(k_space_offset):
        """
        Generates a dictionary describing the ghosting artifact model of the simulated acquisition
        :param k_space_offset: offset intensity of the ghost image
        :type k_space_offset: float
        :return: A dictionary describing the ghosting model
        :rtype: dict
        """
        return {"descr": "addghosts", "kspaceLineOffset": k_space_offset, "value": True}

    @staticmethod
    def generate_signal_spikes_model(number_of_spikes, scale):
        """
        Generates a dictionary describing the signal spike artifact model of the simulated acquisition
        :param number_of_spikes: number of randomly occurring spikes in the signal
        :type number_of_spikes: int
        :param scale: amplitude of the spikes relative to the largest value in the signal
        :type scale, float
        :return: A dictionary describing the signal spike model
        :rtype: dict
        """
        return {"descr": "addspikes", "spikesnum": number_of_spikes, "spikesscale": scale, "value": True}

    @staticmethod
    def generate_aliasing_model(fov_shrink_percent):
        """
        Generates a dictionary describing the aliasing artifact model of the simulated acquisition
        :param fov_shrink_percent: percentage of shrinking of the FOV
        :type fov_shrink_percent: float
        :return: A dictionary describing the aliasing model
        :rtype: dict
        """
        return {"descr": "addaliasing", "aliasingfactor": fov_shrink_percent, "value": True}

    @staticmethod
    def generate_gibbs_ringing_model():
        """
        Generates a dictionary describing the gibbs ringing artifact model of the simulated acquisition
        :return: A dictionary describing the gibbs ringing model
        :rtype: dict
        """
        return {"descr": "addringing", "value": True}

    @staticmethod
    def generate_fiber_stick_compartment(diffusivity, t1, t2, compartment_type):
        """
        Generates a stick model for a fiber compartment. Can only be used for the intra or inter axonal compartment.
        :param diffusivity: diffusivity of the compartment (mm^2/s)
        :type diffusivity: float
        :param t1: T1 relaxation time of the compartment (ms)
        :type t1: int
        :param t2: T2 relaxation time of the compartment (ms)
        :type t2: int
        :param compartment_type: simulation compartment to which links the model (see CompartmentType enum)
        :type compartment_type: CompartmentType
        :return: A dictionary describing the stick model
        :rtype: dict
        """
        assert compartment_type in [
            SimulationFactory.CompartmentType.INTRA_AXONAL, SimulationFactory.CompartmentType.INTER_AXONAL
        ]
        return {
            "type": "fiber",
            "model": "stick",
            "d": diffusivity,
            "t1": t1,
            "t2": t2,
            "ID": compartment_type.value
        }

    @staticmethod
    def generate_fiber_tensor_compartment(d1, d2, d3, t1, t2, compartment_type):
        assert compartment_type in [
            SimulationFactory.CompartmentType.INTRA_AXONAL, SimulationFactory.CompartmentType.INTER_AXONAL
        ]
        return {
            "type": "fiber",
            "model": "tensor",
            "d1": d1,
            "d2": d2,
            "d3": d3,
            "t1": t1,
            "t2": t2,
            "ID": compartment_type.value
        }

    @staticmethod
    def generate_extra_ball_compartment(diffusivity, t1, t2, compartment_type):
        assert compartment_type in [
            SimulationFactory.CompartmentType.EXTRA_AXONAL_1, SimulationFactory.CompartmentType.EXTRA_AXONAL_2
        ]
        return {
            "type": "non-fiber",
            "model": "ball",
            "d": diffusivity,
            "t1": t1,
            "t2": t2,
            "ID": compartment_type.value
        }