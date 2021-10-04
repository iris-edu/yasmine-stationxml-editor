# ****************************************************************************
#
# This file is part of the yasmine editing tool.
#
# yasmine (Yet Another Station Metadata INformation Editor), a tool to
# create and edit station metadata information in FDSN stationXML format,
# is a common development of IRIS and RESIF.
# Development and addition of new features is shared and agreed between * IRIS and RESIF.
#
#
# Version 1.0 of the software was funded by SAGE, a major facility fully
# funded by the National Science Foundation (EAR-1261681-SAGE),
# development done by ISTI and led by IRIS Data Services.
# Version 2.0 of the software was funded by CNRS and development led by * RESIF.
#
# This program is free software; you can redistribute it
# and/or modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version. *
# This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License (GNU-LGPL) for more details. *
# You should have received a copy of the GNU Lesser General Public
# License along with this software. If not, see
# <https://www.gnu.org/licenses/>
#
#
# 2019/10/07 : version 2.0.0 initial commit
#
# ****************************************************************************/


from obspy.core.inventory import Response
from obspy.core.inventory.response import ResponseStage, PolesZerosResponseStage, InstrumentSensitivity
from obspy.core.inventory.response import PolynomialResponseStage
from obspy.core.inventory.response import CoefficientsTypeResponseStage
from obspy.core.inventory.response import InstrumentPolynomial

from obspy.core.inventory.response import CoefficientWithUncertainties
from obspy.core.util.obspy_types import FloatWithUncertainties
from obspy.core.util.obspy_types import FloatWithUncertaintiesAndUnit

from obspy.clients.fdsn.client import Client
from obspy.core.utcdatetime import UTCDateTime

import math

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

A0_PERCENT_DIFF_THRESHOLD = 5.


class IalChannelResponseBuilder:
    def build(self, sensor_dict_list, datalogger_dict_list):
        """
        build an obspy Response object from sensor + datalogger dicts derived from PZYaml files

        :type sensor_dict_list: list of dict // for most (all ?) sensor cases len(list) = 1
        :param sensor_dict_list: Ial sensor dicts from PZYaml file
        :type datalogger_dict_list: list of dict
        :param datalogger_dict_list: Ial datalogger dicts from PZYaml file

        Returns:
        response: obspy.core.inventory.Response object
        """

        fname = "IalChannelResponseBuilder"

        if len(sensor_dict_list) != 1:
            logger.error("%s: sensor_dict_list contains n=%d yaml dicts --> Expecting n=1!" %
                         (fname, len(sensor_dict_list)))
            return None
        sensor_response = sensor_dict_list[0]

        stages = sensor_response['response']['stages']

        if stages is None:
            logger.error("%s: sensor_response contains 0 stages!" % fname)
            return None

        if len(stages) > 1:
            logger.warning("%s: Unexpected sensor_response contains [%d] stages > 1! Only using 1st stage" %
                           (fname, len(stages)))

        stage = sensor_response['response']['stages'][0]
        stage1 = self.stage_dict_to_ResponseStage(stage, stage_sequence_number=1, isSensorResponse=True)

        response_stages = [stage1]

        # MTH: This is a temp hack:
        for i, stage in enumerate(datalogger_dict_list[1]['response']['stages']):
            # print(stage)
            if i in [4, 3]:
                # stage['gain'] = {}
                # stage['gain']['value'] = 1.0
                # stage['gain']['frequency'] = 1.0
                stage['input_units'] = {'name': 'COUNTS', 'description': 'DIGITAL COUNTS'}
                stage['output_units'] = {'name': 'COUNTS', 'description': 'DIGITAL COUNTS'}
            if i == 4:
                stage['gain'] = {}
                stage['gain']['value'] = 1.0
                stage['gain']['frequency'] = 1.0
                if len(stage['extras']) == 0:
                    extras = {}
                    stage['extras'].append(extras)

                # extras['Transfer_normalization_constant'] = 1.0
                # extras['Transfer_normalization_frequency'] = 1.0
                # stage['extras'][0]['Transfer_normalization_frequency'] = 1.0
                # stage['extras'][0]['Transfer_normalization_frequency'] = 1.0

        if len(datalogger_dict_list) == 1:
            logger.debug("%s: n=1 datalogger dict - everything seems to come from 1 file" % fname)
            datalogger_response = datalogger_dict_list[0]
            # Insert generic (gain=1.0) pre-amp stage at stage_number=2:
            response_stages.append(self.get_preamp_stage(stage_sequence_number=2))
        elif len(datalogger_dict_list) == 2:
            logger.debug("%s: n=2 datalogger dicts - I assume this is: pre-amp + digitizer" % fname)
            found_preamp = False
            for i, dict in enumerate(datalogger_dict_list):
                if len(dict['response']['stages']) == 1 and \
                       'AMPLIFIER' in dict['response']['stages'][0]['name']:
                    preamp_stage_number = i
                    found_preamp = True
                    break
            if not found_preamp:
                logger.info("%s: pre-amp stage not found --> What is this ?" % fname)
                return None

            # Convert pre-amp stage into stage_number=2:
            response_stages.append(self.get_preamp_stage_from_dict(
                datalogger_dict_list[preamp_stage_number]['response']['stages'][0],
                stage_sequence_number=2))

            datalogger_dict_list.pop(preamp_stage_number)
            datalogger_response = datalogger_dict_list[0]

        else:
            logger.error("%s: Datalogger list len=%d is > 2 (=max expected)!" %
                         (fname, len(datalogger_dict_list)))

        '''
        # MTH: Experimental return of just sensor response:
        if datalogger_response is None:
            input_units = stage1.input_units
            output_units = stage1.output_units
            sensitivity = InstrumentSensitivity(stage1.stage_gain, 1.0, input_units=input_units,
                                                output_units=output_units)
            response = Response(response_stages=response_stages, instrument_sensitivity=sensitivity)
            return response
        '''

        stages = datalogger_response['response']['stages']
        stage_sequence_number = 3
        net_gain = 1.

        if len(stages) == 1:
            logger.info("Datalogger response has a SINGLE Stage name:%s filter_type:%s" %
                        (stages[0]['name'], stages[0]['filter']['type']))
            # Copy stage output sample rate to input sample rate
            stages[0]['input_sample_rate'] = stages[0]['output_sample_rate']

        for i, stage in enumerate(stages):
            response_stage = self.stage_dict_to_ResponseStage(stage, stage_sequence_number)
            response_stages.append(response_stage)
            if response_stage.stage_gain > 0:
                # print("[%d] gain=%f" % (i, response_stage.stage_gain))
                net_gain *= response_stage.stage_gain
                # print("Convert response_stage:%d stage_sequence_number:%d input_srate:%s" %
                #   (i, stage_sequence_number, response_stage.decimation_input_sample_rate))

            stage_sequence_number += 1

        if isinstance(stage1, PolynomialResponseStage):
            logger.debug("This is a PolynomialResponseStage --> Create InstrumentPolynomial")
            instrument_polynomial = self.get_instrument_polynomial(stage1, net_gain)
            response = Response(response_stages=response_stages,
                                instrument_polynomial=instrument_polynomial)
        else:
            logger.debug("This is NOT a PolynomialResponseStage --> Create InstrumentSensitivity")
            stage0_gain = response_stages[0].stage_gain * response_stages[1].stage_gain
            input_units = response_stages[0].input_units
            output_units = response_stages[1].output_units
        # class InstrumentSensitivity(value, frequency, input_units, output_units,.
            sensitivity = InstrumentSensitivity(stage0_gain, 1.0, input_units=input_units,
                                                output_units=output_units)
            response = Response(response_stages=response_stages,
                                instrument_sensitivity=sensitivity)

            for stage in response.response_stages:
                print(stage)
            # MTH: 2020-07-29: The AROL datalogger stages all have stage_gain_frequency = 0.
            #  So at what frequency should the overall response be calibrated ?
            #  For now, choose f=1.0Hz to match the NRL
            response.recalculate_overall_sensitivity(frequency=1.0)

        return response

    @staticmethod
    def get_preamp_stage_from_dict(stage_dict, stage_sequence_number):
        stage_gain = 1.
        stage_gain_frequency = 1.
        input_units = 'V'
        output_units = 'V'
        name = 'Preamp Stage'
        input_units_description = 'VOLTS'
        output_units_description = 'VOLTS'
        if 'gain' in stage_dict:
            stage_gain = float(stage_dict['gain']['value'])
            stage_gain_frequency = float(stage_dict['gain']['frequency'])
        if 'input_units' in stage_dict:
            input_units = stage_dict['input_units']['name']
            input_units_description = stage_dict['input_units']['description']
        if 'output_units' in stage_dict:
            output_units = stage_dict['output_units']['name']
            output_units_description = stage_dict['output_units']['description']
        if 'name' in stage_dict:
            name = stage_dict['name'].strip()

        preamp_stage = ResponseStage(
                            stage_sequence_number,
                            stage_gain,
                            stage_gain_frequency,
                            input_units, output_units,
                            resource_id=None, resource_id2=None,
                            name=name,
                            input_units_description=input_units_description,
                            output_units_description=output_units_description
                            )
        return preamp_stage

    @staticmethod
    def get_preamp_stage(stage_sequence_number):
        stage_gain = 1.
        stage_gain_frequency = 1.
        input_units = 'V'
        output_units = 'V'
        name = 'Generic Preamp Stage'
        input_units_description = 'VOLTS'
        output_units_description = 'VOLTS'
        preamp_stage = ResponseStage(
                            stage_sequence_number,
                            stage_gain,
                            stage_gain_frequency,
                            input_units, output_units,
                            resource_id=None, resource_id2=None,
                            name=name,
                            input_units_description=input_units_description,
                            output_units_description=output_units_description
                            )
        return preamp_stage

    @staticmethod
    def get_instrument_polynomial(polynomial_stage, g0):

        # MTH: If it becomes necessary to include coefficient errors
        #      in the polezero/fir/etc stages, they will need to
        #      be modified as below, wher CoefficientWithUncertainties replaces float

        scaled_coefficients = []
        for i, coeff in enumerate(polynomial_stage.coefficients):
            scale = 1./g0**float(i)
            value = coeff * scale
            lower_uncertainty = None
            upper_uncertainty = None
            if coeff.lower_uncertainty is not None:
                lower_uncertainty = coeff.lower_uncertainty * scale
            if coeff.upper_uncertainty is not None:
                upper_uncertainty = coeff.upper_uncertainty * scale

            new_coeff = CoefficientWithUncertainties(value,
                                                     lower_uncertainty=lower_uncertainty,
                                                     upper_uncertainty=upper_uncertainty)

            scaled_coefficients.append(new_coeff)

        # This expresses the whole response from
        #   input=Ground motion --> Volts --> recorded COUNTS=output
        output_units = 'COUNTS'
        output_units_description = 'Digital Counts'
        instrument_polynomial = InstrumentPolynomial(
                    polynomial_stage.input_units,
                    output_units,
                    polynomial_stage.frequency_lower_bound,
                    polynomial_stage.frequency_upper_bound,
                    polynomial_stage.approximation_lower_bound,
                    polynomial_stage.approximation_upper_bound,
                    polynomial_stage.maximum_error,
                    scaled_coefficients,
                    approximation_type=polynomial_stage.approximation_type,
                    resource_id=None,
                    name="InstrumentPolynomial",
                    input_units_description=polynomial_stage.input_units_description,
                    output_units_description=output_units_description,
                    description=polynomial_stage.description)

        return instrument_polynomial

    @staticmethod
    def stage_dict_to_ResponseStage(stage, stage_sequence_number, isSensorResponse=False):

        fname = "IalChannelResponseBuilder"

        name = None
        description = None
        if 'name' in stage:
            name = stage['name']
        if 'description' in stage:
            description = stage['description']

        logger.debug("%s: Convert stage:%s [%s]" % (fname, name, description))

        input_units = None
        if 'input_units' in stage and 'name' in stage['input_units']:
            input_units = stage['input_units']['name']
            input_units_description = stage['input_units'].get('description', None)

        output_units = None
        if 'output_units' in stage and 'name' in stage['output_units']:
            output_units = stage['output_units']['name']
            output_units_description = stage['output_units'].get('description', None)

        stage_gain = 1.
        stage_gain_frequency = 0.

        if 'gain' in stage and 'value' in stage['gain']:
            stage_gain = float(stage['gain']['value'])
            stage_gain_frequency = float(stage['gain'].get('frequency', 0.0))

        decimation_input_sample_rate = float(stage.get('input_sample_rate', 0.))
        decimation_output_sample_rate = float(stage.get('output_sample_rate', 0.))
        decimation_factor = int(stage.get('decimation_factor', 1))

        decimation_delay = 0
        # The estimated pure delay (seconds) for the stage
        if 'decimation_delay' in stage:
            decimation_delay = float(stage.get('decimation_delay', 0.0))

        # decimation_offset is the # of samples offset chosen.
        # Should have 0 <= decimation_offset < decimation_factor
        decimation_offset = 0
        if 'decimation_offset' in stage:
            decimation_offset = int(stage.get('decimation_offset', 0))
        elif 'offset' in stage:
            decimation_offset = int(stage.get('offset', 0))

        decimation_correction = float(stage.get('decimation_correction', 0.))

        filter_type = None
        if 'filter' in stage:
            filter_type = stage['filter']['type'].upper()

        logger.debug("[%2d]: name=[%s] ftype=[%s] i_units=[%s] o_units=[%s] gain=[%s] i_srate=[%.1f] o_srate=[%.1f] dec_fac=[%d]" %
                     (stage_sequence_number, name, filter_type, input_units, output_units, stage_gain,
                      decimation_input_sample_rate, decimation_output_sample_rate, decimation_factor))

        if filter_type == 'POLESZEROS' or filter_type == 'ANALOG':

            pzs = stage['filter']

            allowable_pz_transfer_function_types = {"LAPLACE (RADIANS/SECOND)": "A",
                                                    "LAPLACE (HERTZ)": "B",
                                                    "DIGITAL (Z-TRANSFORM)": "D"}

            if 'transfer_function_type' in pzs:
                pz_transfer_function_type = pzs['transfer_function_type']
            # This is a temporary fix to keep AROL lib from breaking until it is updated
            elif 'units' in pzs:
                if 'RAD' in pzs['units'].upper():
                    pz_transfer_function_type = "LAPLACE (RADIANS/SECOND)"
                elif 'HERTZ' in pzs['units'].upper() or 'HZ' in pzs['units'].upper():
                    pz_transfer_function_type = "LAPLACE (HERTZ)"
                elif 'DIGITAL' in pzs['units'].upper():
                    pz_transfer_function_type = "DIGITAL (Z-TRANSFORM)"
                else:
                    pz_transfer_function_type = pzs['units']
            else:
                pz_transfer_function_type = "UNSPECIFIED"

            if pz_transfer_function_type not in allowable_pz_transfer_function_types:
                logger.error("Unable to decipher pz_transfer_function_type=[%s] --> Skipping!" %
                             (pz_transfer_function_type))
                return None

            pz_type = allowable_pz_transfer_function_types[pz_transfer_function_type]

            poles = []
            if 'poles' in pzs:
                for pole in pzs['poles']:
                    # Catching ANALOG filter where poles/zeros are strings:
                    if isinstance(pole, str):
                        # -1186.34+1136.68j
                        poles.append(complex(pole))
                    else:
                        poles.append(complex(pole[0], pole[1]))

            zeros = []
            if 'zeros' in pzs:
                for zero in pzs['zeros']:
                    if isinstance(zero, str):
                        zeros.append(complex(zero))
                    else:
                        zeros.append(complex(zero[0], zero[1]))

            # MTH: It's possible that any param (e.g., Transfer_normalization_constant) may be
            #      present in more than one stage['extras'] dict, so which one trumps ?
            nominal_A0 = 1.
            nominal_f0 = 0.
            for extras in stage['extras']:
                if 'Transfer_normalization_constant' in extras:
                    nominal_A0 = float(extras['Transfer_normalization_constant'])
                    logger.info("Found nominal_A0:%f" % nominal_A0)
                if 'Transfer_normalization_frequency' in extras:
                    nominal_f0 = float(extras['Transfer_normalization_frequency'])
                    logger.info("Found nominal_f0:%f" % nominal_f0)

            normlization_frequency = 0.
            if nominal_f0 > 0.:
                normalization_frequency = nominal_f0
            else:
                normalization_frequency = stage_gain_frequency
                logger.warning("%s: polezero stage norm frequency NOT set!  Using stage_gain_frequency:%f" %
                               (fname, stage_gain_frequency))

            A0 = IalChannelResponseBuilder.getNormalization(normalization_frequency, poles, zeros, pz_type)
            normalization_factor = A0

            if nominal_A0 > 1:
                logger.info('   Nominal A0:%f' % nominal_A0)
                logger.info('Calculated A0:%f' % A0)
                percent_diff = 100. * abs(A0 - nominal_A0)/nominal_A0
                logger.info('Percent diff:%f' % percent_diff)
                if percent_diff >= A0_PERCENT_DIFF_THRESHOLD:
                    logger.warning('A0_normalization Percent diff:%f --> Exceeds threshold:%f' %
                                   (percent_diff, A0_PERCENT_DIFF_THRESHOLD))

            response_stage = PolesZerosResponseStage(
                                stage_sequence_number,
                                stage_gain,
                                stage_gain_frequency,
                                input_units, output_units,
                                pz_transfer_function_type,
                                normalization_frequency,
                                zeros,
                                poles,
                                normalization_factor,
                                resource_id=None, resource_id2=None,
                                name=name,
                                input_units_description=input_units_description,
                                output_units_description=output_units_description,
                                description=description,
                                decimation_input_sample_rate=decimation_input_sample_rate,
                                decimation_factor=decimation_factor,
                                decimation_offset=decimation_offset,
                                decimation_delay=decimation_delay,
                                decimation_correction=decimation_correction)

        elif filter_type == 'POLYNOMIAL':

            polynomial_stage = stage
            frequency_lower_bound = 0
            frequency_upper_bound = 0
            # MTH: these will likely need implementation once yaml lib is more complete:
            approximation_type = 'MACLAURIN'
            approximation_lower_bound = 0
            approximation_upper_bound = 0
            maximum_error = 0

            keys = {'approximation_type', 'ApproximationType'}
            for k in keys:
                if k in polynomial_stage:
                    approximation_type = polynomial_stage[k]
                    break

            keys = {'frequency_lower_bound', 'FrequencyLowerBound'}
            for k in keys:
                if k in polynomial_stage:
                    frequency_lower_bound = float(polynomial_stage[k])
                    break

            keys = {'frequency_upper_bound', 'FrequencyUpperBound'}
            for k in keys:
                if k in polynomial_stage:
                    frequency_upper_bound = float(polynomial_stage[k])
                    break

            keys = {'maximum_error', 'MaximumError'}
            for k in keys:
                if k in polynomial_stage:
                    maximum_error = float(polynomial_stage[k])
                    break

            # There's a lot of variation
            # arol: lower_bound_approximation
            # obspy: approximation_lower_bound
            # fdsn:  ApproximationLowerBound
            keys = {'approximation_lower_bound', 'Approximation_Lower_Bound', 'ApproximationLowerBound',
                    'lower_bound_approximation', 'Lower_Bound_Approximation',
                    }
            for k in keys:
                if k in polynomial_stage:
                    approximation_lower_bound = float(polynomial_stage[k])
                    break

            keys = {'approximation_upper_bound', 'Approximation_Upper_Bound', 'ApproximationUpperBound',
                    'upper_bound_approximation', 'Upper_Bound_Approximation',
                    }
            for k in keys:
                if k in polynomial_stage:
                    approximation_upper_bound = float(polynomial_stage[k])
                    break

            if 'coefficients' in stage['filter']:
                coefficients = []
                for i, string in enumerate(stage['filter']['coefficients']):
                    try:
                        # val = FloatWithUncertainties(float(string),
                        # MTH: Update this if/when uncertainties become available:
                        val = CoefficientWithUncertainties(float(string),
                                                           lower_uncertainty=None,
                                                           upper_uncertainty=None,
                                                           )
                        coefficients.append(val)
                        # coefficients.append(float(string))
                    except ValueError:
                        logger.error("Polynomial Coefficients: Unable to scan float from str=[%s]" %
                                     string)

            # MTH: another work around might be to set the (parent) gain of this stage = 1
            #      so that the stage0 gain (InstrumentSensitivity) is just the datalogger stages

            stage_gain = None
            stage_gain_frequency = None

            response_stage = PolynomialResponseStage(
                                stage_sequence_number,
                                stage_gain,
                                stage_gain_frequency,
                                input_units, output_units,
                                frequency_lower_bound,
                                frequency_upper_bound,
                                approximation_lower_bound,
                                approximation_upper_bound,
                                maximum_error,
                                coefficients,
                                approximation_type=approximation_type,
                                resource_id=None, resource_id2=None,
                                name=name,
                                input_units_description=input_units_description,
                                output_units_description=output_units_description,
                                description=description
                                )

        elif filter_type in ['ADConversion', 'AD_CONVERSION'] or filter_type == 'FIR':

            ''' cf_transfer_function_type may be one of:

                * ``ANALOG (RADIANS/SECOND)``
                * ``ANALOG (HERTZ)``
                * ``DIGITAL``
            '''

            cf_transfer_function_type = 'DIGITAL'

            if filter_type in ['ADConversion', 'AD_CONVERSION']:
                numerator = [FloatWithUncertaintiesAndUnit(1.0)]
            else:
                if 'coefficients' in stage['filter']:
                    coefficients = stage['filter']['coefficients']
                    numerator = []
                    for x in coefficients:
                        numerator.append(FloatWithUncertaintiesAndUnit(x, lower_uncertainty=None,
                                         upper_uncertainty=None, unit=None)
                                         )
                # MTH: We are assuming all these coeffs get stuffed into the *numerator*
                #      check if this is *not* the case
                    if 'extras' in stage['filter'] and 'Number_of_zeros' in stage['filter']['extras']:
                        if stage['filter']['extras']['Number_of_zeros'] != len(numerator):
                            logger.warning("%s: FIR stage:%d yaml #zeros=%d != #coefficients=%d !" %
                                           (fname, stage_sequence_number, stage['filter']['extras']['Number_of_zeros'],
                                            len(numerator)))

                # MTH: Temp hack since the yaml files have the *wrong* input units for DECIMATION stages
                input_units = 'counts'
                output_units = 'counts'

            response_stage = CoefficientsTypeResponseStage(
                                stage_sequence_number, stage_gain,
                                stage_gain_frequency, input_units, output_units,
                                cf_transfer_function_type,
                                numerator=numerator,
                                denominator=[],
                                resource_id=None,
                                resource_id2=None,
                                name=name,
                                input_units_description=input_units_description,
                                output_units_description=output_units_description,
                                description=description,
                                decimation_input_sample_rate=decimation_input_sample_rate,
                                decimation_factor=decimation_factor,
                                decimation_offset=decimation_offset,
                                decimation_delay=decimation_delay,
                                decimation_correction=decimation_correction)

        else:
            logger.error("%s: Unknown filter_type=[%s] --> return None!" % (fname, filter_type))
            response_stage = None

        return response_stage

    @staticmethod
    def getNormalization(f0, poles, zeros, pz_type):

        s = 0.000 + 1.000j
        numerator = 1.000 + 0.000j
        denominator = 1.000 + 0.000j

        if pz_type == 'B':
            s *= f0
        else:
            s *= 2.*np.pi*f0

        for zero in zeros:
            numerator *= (s - zero)

        for pole in poles:
            denominator *= (s - pole)

        Gf = numerator / denominator
        # print(Gf)
        # print(abs(Gf))
        A0 = 1./abs(Gf)

        return A0
