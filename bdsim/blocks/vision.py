import logging
import numpy as np
from bdsim.components import SourceBlock, SinkBlock, FunctionBlock, SubsystemBlock, block
from bdsim.tuning import TunableBlock
from bdsim.tuning.parameter import HyperParam, RangeParam

try:
    import cv2

    @block
    class Camera(SourceBlock):
        """
        :blockname:`CAMERA`

        .. table::
        :align: left

        +--------+---------+---------+
        | inputs | outputs |  states |
        +--------+---------+---------+
        | 0      | 1       | 0       |
        +--------+---------+---------+
        |        | float,  |         |
        |        | A(N,)   |         |
        +--------+---------+---------+
        """

        type = "camera"

        def __init__(self, source, *cv2_args, **kwargs):
            """
            :param source: the source of the video stream. A local camera device index or a path/url.
                If a video file is specified, will play the file (works in simulation mode).
            :type source: Union[int, string]
            :param `*cv2_args`: Optional arguments to pass into `cv2's VideoCapture constructor`
            <https://docs.opencv.org/4.1.0/d8/dfe/classcv_1_1VideoCapture.html#ac4107fb146a762454a8a87715d9b7c96>
            :param ``**kwargs``: common Block options
            :return: a VIDEOCAPTURE block
            :rtype: VideoCapture instance

            Creates a VideoCapture block.

            Examples::
                TODO

            See `the OpenCV4.1 docs`
            <https://docs.opencv.org/4.1.0/d8/dfe/classcv_1_1VideoCapture.html>
            for further detail.
            """
            super().__init__(nout=1, **kwargs)
            self.is_livestream = isinstance(source, int)
            if not (self.is_livestream or isinstance(source, str)):
                # coerce it into str, good if it's something like a pathlib.Path
                source = str(source)
            self.video_capture = cv2.VideoCapture(source, *cv2_args)
            assert (
                self.video_capture.isOpened()
            ), "VideoCapture at {source} could not be opened." \
                "Please check the filepath / if another process is using the camera" \
                .format(source=source)

        def start(self, **kwargs):
            super().start(**kwargs)
            if not self.is_livestream:
                # restart the video if it is
                self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)

        def output(self, t=None):
            # set the frame if we're using a video
            if t is not None and not self.is_livestream:
                fps = self.video_capture.get(cv2.CAP_PROP_FPS)
                frame_n = int(round(t * fps))
                self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_n)

            _, frame = self.video_capture.read()
            assert frame is not None, "An unknown error occured in OpenCV: camera disconnected or video file ended"
            return [frame]

    @block
    class CvtColor(FunctionBlock):

        type = "cvtcolor"

        # TODO: automate 'from_', when unit system is implemented ('rgb pixel' will be a unit)

        def __init__(self, input, cvt_code, **kwargs):
            super().__init__(inputs=[input], nin=1, nout=1, **kwargs)
            self.cvt_code = cvt_code

        def output(self, _t=None):
            [input] = self.inputs
            try:
                converted = cv2.cvtColor(input, self.cvt_code)
            except AttributeError as e:
                raise Exception(
                    "Available methods are: {methods}".format(
                        methods=', '.join(
                            attr for attr in dir(cv2)
                            if attr.startswith('COLOR_'))
                    )
                ) from e
            return [converted]

    @block
    class InRange(FunctionBlock, TunableBlock):

        type = "inrange"

        def __init__(self, input, lower=(0, 0, 0), upper=(255, 255, 255), **kwargs):
            super().__init__(inputs=[input], nin=1, nout=1, **kwargs)

            self.lower = self._param('lower', lower,
                                     min=np.array((0, 0, 0)), max=np.array((255, 255, 255)))
            self.upper = self._param('upper', upper,
                                     min=np.array((0, 0, 0)), max=np.array((255, 255, 255)))

        def output(self, _t=None):
            [input] = self.inputs
            mask = cv2.inRange(input, self.lower, self.upper)
            return [mask]

    @block
    class Mask(FunctionBlock):
        type = "mask"

        def __init__(self, input, **kwargs):
            super().__init__(inputs=[input], nin=2, nout=1, **kwargs)

        def output(self, _t=None):
            [input, mask] = self.inputs
            masked = cv2.bitwise_and(input, input, mask=mask)
            return [masked]

    @block
    class Threshold(FunctionBlock):

        type = "threshold"
        available_methods = [
            "binary",
            "binary_inv",
            "trunc",
            "tozero",
            "tozero_inv",
            "mask",
        ]
        # TODO support "otsu" & "triangle"

        def __init__(self, input, lower, upper, method="binary", **kwargs):
            super().__init__(inputs=[input], nin=1, nout=1, **kwargs)
            assert (
                method in self.available_methods
            ), "Thresholding method {method} unsupported. Please select from methods in Threshold.available_methods list" \
                .format(method=method)

            for l, u in zip(lower, upper):
                assert l <= u, "all lower vals must be less than corresponding upper"

            self.lower = lower
            self.upper = upper
            self.method = getattr(
                cv2, "THRESH_{method}".format(method=method.upper()))

        def output(self, _t=None):
            [input] = self.inputs
            _, output = cv2.threshold(
                input, self.lower, self.upper, self.method)
            return [output]

    class KernelParam2D(HyperParam):

        available_types = ["ellipse", "rect", "cross"]

        def __init__(self, spec=("ellipse", 3, 3), **kwargs):
            super().__init__(spec, **kwargs)

            type, width, height = spec if isinstance(spec, tuple) else \
                ("custom", *spec.shape) if isinstance(spec, np.ndarray) else \
                (None, None, None)

            # self.array = self.param('array', self.val if type == 'custom' else None)
            self.type = self.param(
                'type', type, oneof=self.available_types)
            self.width = self.param('width', width, min=3, max=12)
            self.height = self.param('height', height, min=3, max=12)
            self.update()

        def update(self, _=None):
            # TODO: allow for custom kernel with matrix editor (see commented out code)
            # if type == "custom":
            #     # self.show(self.array)
            #     self.hide(self.width, self.height)
            # else:
            assert (
                self.type in self.available_types
            ), "Morphological Kernel type {type} unsupported. Please select from {types}" \
                .format(type=self.type, types=self.available_types)

            # self.show('width', 'height')
            # self.hide(self.array)

            # self.array.set_val(cv2.getStructuringElement(
            #         getattr(cv2, "MORPH_%s" % type.upper()),
            #         (self.width.val, self.height.val)
            #     ), exclude_cb=self.setup_kernel)

            # self.val = self.array.val
            self.val = cv2.getStructuringElement(
                getattr(cv2, "MORPH_%s" % self.type.upper()),
                (self.width, self.height)
            )

    class _Morphological(FunctionBlock, TunableBlock):
        type = "morphological"

        def __init__(self, input, diadic_func, kernel, iterations, **kwargs):
            super().__init__(inputs=[input]
                             if input else [], nin=1, nout=1, **kwargs)

            self.diadic_func = diadic_func
            self.kernel = self._param('kernel', KernelParam2D(kernel))
            self.iterations = self._param(
                'iterations', iterations, min=1, max=10)

        def output(self, _t=None):
            [input] = self.inputs
            output = self.diadic_func(input, self.kernel, self.iterations)
            return [output]

    @block
    class Erode(_Morphological):

        type = "erode"

        def __init__(self, input, iterations=1, kernel=("ellipse", 3, 3), **kwargs):
            super().__init__(
                input,
                diadic_func=cv2.erode,
                kernel=kernel,
                iterations=iterations,
                **kwargs,
            )

    @block
    class Dilate(_Morphological):

        type = "dilate"

        def __init__(self, input, iterations=1, kernel=("ellipse", 3, 3), **kwargs):
            super().__init__(
                input,
                diadic_func=cv2.dilate,
                kernel=kernel,
                iterations=iterations,
                **kwargs,
            )

    @block
    class OpenMask(SubsystemBlock, TunableBlock):

        type = "openmask"

        def __init__(self, input, iterations=1, kernel=("ellipse", 3, 3), **kwargs):
            super().__init__(
                inputs=[input],
                nin=1,
                nout=1,
                **kwargs
            )

            morphblock_kwargs = dict(input=None,
                                     kernel=self._param(
                                         'kernel', KernelParam2D(kernel), ret_param=True),
                                     iterations=self._param(
                                         'iterations', iterations, min=1, max=10, ret_param=True),
                                     bd=self.bd, is_subblock=True)

            # I would expect cv2.morphologyEx() to be faster than an cv2.erode -> cv2.dilate
            # but preliminary benchmarks show this isn't the case.
            self.dilate = Dilate(**morphblock_kwargs)
            self.erode = Erode(**morphblock_kwargs)

        def output(self, _t=None):
            self.erode.inputs = self.inputs
            eroded = self.erode.output()
            self.dilate.inputs = eroded
            return self.dilate.output()

    @block
    class CloseMask(SubsystemBlock, TunableBlock):

        type = "closemask"

        def __init__(self, input, iterations=1, kernel=("ellipse", 3, 3), **kwargs):
            # TODO Propagate name in some way to aid debugging
            super().__init__(
                inputs=[input],
                nin=1,
                nout=1,
                **kwargs
            )
            args = dict(input=None, tinker=kwargs['tinker'],
                        kernel=self._param('kernel', kernel),
                        iterations=self._param(
                            'iterations', iterations, min=1, max=10),
                        bd=self.bd, is_subblock=True)

            self.dilate = Dilate(**args)
            self.erode = Erode(**args)

        def output(self, _t=None):
            self.dilate.inputs = self.inputs
            dilated = self.dilate.output()
            self.erode.inputs = dilated
            return self.erode.output()

    @block
    class Blobs(FunctionBlock, TunableBlock):
        """[summary]

        :param Block: [description]
        :type Block: [type]

        grayscale_threshold: only useful if input is grayscale
            (min, max, step) TODO describe this better
            https://github.com/opencv/opencv/blob/e5e767abc1314f918a848e0b912dc9574c19bfaf/modules/features2d/src/blobdetector.cpp#L324

        Would be nice to represent this as a subsystem block rather than a single function block,
        ie if/when a gui is developed (for education purposes), but it would be (slightly) less efficient,

        some SimpleBlobDetector features, such as color filtering, don't make sense (always 255/0 for binary image), so was omitted.
        See: https://github.com/opencv/opencv/blob/e5e767abc1314f918a848e0b912dc9574c19bfaf/modules/features2d/src/blobdetector.cpp#L275
        """

        type = "blobs"

        def __init__(
            self,
            input,
            top_k=None,
            min_dist_between_blobs=10,
            area=None,
            circularity=None,
            inertia_ratio=None,
            convexivity=None,
            grayscale_threshold=(50, 220, 10),
            **kwargs
        ):
            super().__init__(inputs=[input], nin=1, nout=1, **kwargs)

            self.top_k = self._param('top_k', top_k, min=1, max=10, default=1)

            self.min_dist_between_blobs = self._sbd_param('min_dist_between_blobs',
                                                          min_dist_between_blobs, min=0, max=1e3, log_scale=2)
            self.area = self._sbd_param('area', RangeParam(
                area, min=1, max=2**21, default=(50, 2**21), log_scale=True))
            self.circularity = self._sbd_param('circularity', RangeParam(
                circularity, min=0, max=1, default=(0.5, 1)))
            self.inertia_ratio = self._sbd_param('inertia_ratio', RangeParam(
                inertia_ratio, min=0, max=1, default=(0.5, 1)))
            self.convexivity = self._sbd_param('convexivity', RangeParam(
                convexivity, min=0, max=1, default=(0.5, 1)))
            self.grayscale_threshold = self._sbd_param(
                'grayscale_threshold', grayscale_threshold, min=(0, 0, 1), max=(255, 255, 255))

            self._setup_sbd()

        def _sbd_param(self, name, val, **kwargs):
            return self._param(name, val, on_change=self._setup_sbd, **kwargs)

        def _setup_sbd(self, _=None):  # unused param to work with on_change
            params = cv2.SimpleBlobDetector_Params()
            params.minDistBetweenBlobs = self.min_dist_between_blobs
            (
                params.minThreshold,
                params.maxThreshold,
                params.thresholdStep,
            ) = self.grayscale_threshold

            if self.area:
                params.minArea, params.maxArea = self.area
            params.filterByArea = bool(self.area)

            if self.circularity:
                params.minCircularity, params.maxCircularity = self.circularity
            params.filterByCircularity = bool(self.circularity)

            if self.inertia_ratio:
                params.minInertiaRatio, params.maxInertiaRatio = self.inertia_ratio
            params.filterByInertia = bool(self.inertia_ratio)

            self.detector = cv2.SimpleBlobDetector_create(params)

        def output(self, _t=None):
            [input] = self.inputs
            keypoints = self.detector.detect(input)
            return [keypoints[:self.top_k] if self.top_k else keypoints]

    @block
    class Display(SinkBlock):
        """
        :blockname:`DISPLAY`

        .. table::
        :align: left

        +-------------+---------+---------+
        | inputs      | outputs |  states |
        +-------------+---------+---------+
        | 1           | 0       | 0       |
        +-------------+---------+---------+
        | A(H, W, C)  |         |         |
        +-------------+---------+---------+
        """

        type = "display"

        def __init__(self, input, title="Display", **kwargs):
            super().__init__(inputs=[input], nin=1, **kwargs)
            self.title = title

        def step(self):
            [input] = self.inputs
            try:
                cv2.imshow(self.title, input)
                cv2.waitKey(1)  # cv2 needs this to actually show, apparently
            except Exception as e:
                raise Exception(
                    ("Expected input to be an HxW[xC] ndarray, got {input}").format(
                        input=input)
                ) from e

        def stop(self):
            # TODO: Check if overkill to ensure that self.title never changes?
            cv2.destroyWindow(self.title)

    @block
    class DrawKeypoints(FunctionBlock):

        type = "drawkeypoints"

        def __init__(self, image, keypoints, color=(0, 0, 255), **kwargs):
            super().__init__(inputs=[image, keypoints],
                             nin=2, nout=1, **kwargs)
            self.color = color

        def output(self, _t=None):
            [image, keypoints] = self.inputs
            drawn = cv2.drawKeypoints(image, keypoints, np.array([]), self.color,
                                      cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
            return [drawn]

except ImportError:
    logging.warning(
        "OpenCV not installed. Vision blocks will not be available")
