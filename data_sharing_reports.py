# -*- coding: utf-8 -*-
"""
Created on Wed Oct 07 17:31:39 2015

@author: LCameron
"""

import os
import xlrd
from xlutils.copy import copy
from datetime import datetime as dt
from PIL import Image
from shutil import rmtree

template_name = 'Share_1_template.xls'

sheet_map = {'Submission': 0,
             'Meta Data': 1,
             'Baseline': 2,
             'REWS': 3,
             'TI Renorm': 4,
             'REWS and TI Renorm': 5,
             'PDM': 6}

def wrt_cell_keep_style(value, sheet, row, col):
    style = _get_cell_style(sheet, row, col)
    sheet.write(row, col, value)
    _apply_cell_style(style, sheet, row, col)
    
def _get_cell_style(sheet, row, col):
    return sheet._Worksheet__rows.get(row)._Row__cells.get(col).xf_idx
    
def _apply_cell_style(style, sheet, row, col):
    sheet._Worksheet__rows.get(row)._Row__cells.get(col).xf_idx = style


class pcwg_share1_rpt(object):
    
    def __init__(self, analysis, version = 'Unknown', template = template_name, output_fname = (os.getcwd() + os.sep + 'Data Sharing Initiative 1 Report.xls')):
        rb = xlrd.open_workbook(template, formatting_info=True)
        self.workbook = copy(rb)
        self.analysis = analysis
        self.no_of_datasets = len(analysis.datasetConfigs)
        self.output_fname = output_fname
        self.version = version
    
    def report(self):
        self.write_submission_data(sheet_map['Submission'])
        self.write_meta_data()
        self.write_metrics()
        self.insert_images()
        self.export()
    
    def write_meta_data(self):
        sh = self.workbook.get_sheet(sheet_map['Meta Data'])
        col = 2
        used_inner_range = [self.analysis.innerRangeLowerShear, self.analysis.innerRangeUpperShear, self.analysis.innerRangeLowerTurbulence, self.analysis.innerRangeUpperTurbulence]
        range_A = [0.05, 0.25, 0.08, 0.12]
        range_B = [0.05, 0.25, 0.06, 0.1]
        range_C = [0.1, 0.3, 0.1, 0.14]
        if used_inner_range == range_A:
            range_id = 'A'
        elif used_inner_range == range_B:
            range_id = 'B'
        elif used_inner_range == range_C:
            range_id = 'C'
        else:
            raise Exception('The inner range %s is not valid for use in the PCWG Sharing Initiative.' % used_inner_range)
        manual_required_style = _get_cell_style(sh, 7, 2)
        manual_optional_style = _get_cell_style(sh, 13, 2)
        man_req_rows = [7, 11, 12, 18, 19, 21, 26, 29]
        man_opt_rows = [13, 14, 15, 16, 17, 20, 22, 28]
        for conf in self.analysis.datasetConfigs:
            wrt_cell_keep_style(self.analysis.datasetUniqueIds[conf.name]['Configuration'], sh, 6, col)
            if self.analysis.rewsActive:
                wrt_cell_keep_style(len(conf.windSpeedLevels), sh, 8, col)
                wrt_cell_keep_style(len(conf.windDirectionLevels), sh, 9, col)
            wrt_cell_keep_style(range_id, sh, 10, col)
            wrt_cell_keep_style(self.analysis.config.diameter, sh, 23, col)
            wrt_cell_keep_style(self.analysis.config.hubHeight, sh, 24, col)
            wrt_cell_keep_style(self.analysis.config.ratedPower, sh, 25, col)
            wrt_cell_keep_style(int(min(self.analysis.dataFrame.loc[self.analysis.dataFrame[self.analysis.nameColumn] == conf.name, self.analysis.timeStamp].dt.year)), sh, 27, col)
            for row in man_req_rows:
                sh.write(row, col, None)
                _apply_cell_style(manual_required_style, sh, row, col)
            for row in man_opt_rows:
                sh.write(row, col, None)
                _apply_cell_style(manual_optional_style, sh, row, col)
            col += 1
    
    def write_submission_data(self, sheet_no):
        sh = self.workbook.get_sheet(sheet_no)
        wrt_cell_keep_style(self.analysis.uniqueAnalysisId, sh, 5, 2)
        wrt_cell_keep_style(str(dt.now()), sh, 6, 2)
        wrt_cell_keep_style(str(self.version), sh, 7, 2)
        conf_row, ts_row, col = 11, 12, 2
        style = _get_cell_style(sh, conf_row, col)
        for conf_name in self.analysis.datasetUniqueIds.keys():
            sh.write(conf_row, col, self.analysis.datasetUniqueIds[conf_name]['Configuration'])
            _apply_cell_style(style, sh, conf_row, col)
            sh.write(ts_row, col, self.analysis.datasetUniqueIds[conf_name]['Time Series'])
            _apply_cell_style(style, sh, ts_row, col)
            col += 1
        
    def write_metrics(self):
        self._write_metrics_sheet('Baseline', self.analysis.pcwgErrorBaseline)
        if self.analysis.turbRenormActive:
            self._write_metrics_sheet('TI Renorm', self.analysis.pcwgErrorTurbRenor)
        if self.analysis.rewsActive:
            self._write_metrics_sheet('REWS', self.analysis.pcwgErrorRews)
        if (self.analysis.turbRenormActive and self.analysis.rewsActive):
            self._write_metrics_sheet('REWS and TI Renorm', self.analysis.pcwgErrorTiRewsCombined)
        if self.analysis.powerDeviationMatrixActive:
            self._write_metrics_sheet('PDM', self.analysis.pcwgErrorPdm)
    
    def _write_metrics_sheet(self, sh_name, error_col):
        self.__write_overall_metric_sheet(sh_name)
        self.__write_by_ws_metric_sheet(sh_name, error_col)
        self.__write_by_dir_metric_sheet(sh_name, error_col)
        self.__write_by_time_metric_sheet(sh_name, error_col)
        self.__write_by_range_metric_sheet(sh_name, error_col)
        self.__write_by_four_cell_matrix_metric_sheet(sh_name, error_col)
        self.__write_by_month_metric_sheet(sh_name, error_col)
    
    def __write_overall_metric_sheet(self, sh_name):
        sh = self.workbook.get_sheet(sheet_map[sh_name])
        wrt_cell_keep_style(self.analysis.overall_pcwg_err_metrics[self.analysis.dataCount], sh, 3, 3)
        wrt_cell_keep_style(self.analysis.overall_pcwg_err_metrics[sh_name + ' NME'], sh, 4, 3)
        wrt_cell_keep_style(self.analysis.overall_pcwg_err_metrics[sh_name + ' NMAE'], sh, 5, 3)
    
    def __write_by_ws_metric_sheet(self, sh_name, err_col):
        df = self.analysis.binned_pcwg_err_metrics[self.analysis.normalisedWSBin][err_col]
        sh = self.workbook.get_sheet(sheet_map[sh_name])
        col = 3
        for i in self.analysis.normalisedWindSpeedBins.centers:
            try:
                wrt_cell_keep_style(int(df.loc[i, 'Data Count']), sh, 7, col)
                wrt_cell_keep_style(df.loc[i, 'NME'], sh, 8, col)
                wrt_cell_keep_style(df.loc[i, 'NMAE'], sh, 9, col)
                col += 1
            except:
                col += 1
    
    def __write_by_dir_metric_sheet(self, sh_name, err_col):
        df = self.analysis.binned_pcwg_err_metrics[self.analysis.pcwgDirectionBin][err_col]
        sh = self.workbook.get_sheet(sheet_map[sh_name])
        col = 3
        for i in self.analysis.pcwgWindDirBins.centers:
            try:
                wrt_cell_keep_style(int(df.loc[i, 'Data Count']), sh, 19, col)
                wrt_cell_keep_style(df.loc[i, 'NME'], sh, 20, col)
                wrt_cell_keep_style(df.loc[i, 'NMAE'], sh, 21, col)
                col += 1
            except:
                col += 1
    
    def __write_by_time_metric_sheet(self, sh_name, err_col):
        df = self.analysis.binned_pcwg_err_metrics[self.analysis.hourOfDay][err_col]
        sh = self.workbook.get_sheet(sheet_map[sh_name])
        col = 3
        for i in range(0,24):
            try:
                wrt_cell_keep_style(int(df.loc[i, 'Data Count']), sh, 11, col)
                wrt_cell_keep_style(df.loc[i, 'NME'], sh, 12, col)
                wrt_cell_keep_style(df.loc[i, 'NMAE'], sh, 13, col)
                col += 1
            except:
                col += 1
    
    def __write_by_range_metric_sheet(self, sh_name, err_col):
        df = self.analysis.binned_pcwg_err_metrics[self.analysis.pcwgRange][err_col]
        sh = self.workbook.get_sheet(sheet_map[sh_name])
        col = 3
        for i in ['Inner','Outer']:
            try:
                wrt_cell_keep_style(int(df.loc[i, 'Data Count']), sh, 23, col)
                wrt_cell_keep_style(df.loc[i, 'NME'], sh, 24, col)
                wrt_cell_keep_style(df.loc[i, 'NMAE'], sh, 25, col)
                col += 1
            except:
                col += 1
                
    def __write_by_four_cell_matrix_metric_sheet(self, sh_name, err_col):
        df = self.analysis.binned_pcwg_err_metrics[self.analysis.pcwgFourCellMatrixGroup][err_col]
        sh = self.workbook.get_sheet(sheet_map[sh_name])
        col = 3
        for i in ['LWS-LTI','LWS-HTI','HWS-LTI','HWS-HTI']:
            try:
                wrt_cell_keep_style(int(df.loc[i, 'Data Count']), sh, 27, col)
                wrt_cell_keep_style(df.loc[i, 'NME'], sh, 28, col)
                wrt_cell_keep_style(df.loc[i, 'NMAE'], sh, 29, col)
                col += 1
            except:
                col += 1
                
    def __write_by_month_metric_sheet(self, sh_name, err_col):
        df = self.analysis.binned_pcwg_err_metrics[self.analysis.calendarMonth][err_col]
        sh = self.workbook.get_sheet(sheet_map[sh_name])
        col = 3
        for i in range(1,13):
            try:
                wrt_cell_keep_style(int(df.loc[i, 'Data Count']), sh, 15, col)
                wrt_cell_keep_style(df.loc[i, 'NME'], sh, 16, col)
                wrt_cell_keep_style(df.loc[i, 'NMAE'], sh, 17, col)
                col += 1
            except:
                col += 1
    
    def insert_images(self):
        from plots import MatplotlibPlotter
        plt_path = 'Temp'
        plotter = MatplotlibPlotter(plt_path, self.analysis)
        for conf in self.analysis.datasetConfigs:
            sh = self.workbook.add_sheet(conf.name)
            row_filt = (self.analysis.dataFrame[self.analysis.nameColumn] == conf.name)
            fname = conf.name + ' Anonymous Power Curve Plot'
            plotter.plotPowerCurve(self.analysis.inputHubWindSpeed, self.analysis.actualPower, self.analysis.innerMeasuredPowerCurve, anon = True, row_filt = row_filt, fname = fname + '.png', show_analysis_pc = False, mean_title = 'Inner Range Power Curve')
            im = Image.open(plt_path + os.sep + fname + '.png').convert('RGB')
            im.save(plt_path + os.sep + fname + '.bmp')
            sh.write(0, 0, self.analysis.datasetUniqueIds[conf.name]['Configuration'])
            sh.insert_bitmap(plt_path + os.sep + fname + '.bmp' , 2, 1)
        try:
            rmtree(plt_path)
        except:
            print 'Could not delete folder %s' % (os.getcwd() + os.sep + plt_path)
            
    
    def export(self):
        self._write_confirmation_of_export()
        print "Exporting the PCWG Share 1 report to:\n\t%s" % (self.output_fname)
        self.workbook.save(self.output_fname)

    def _write_confirmation_of_export(self):
        sh = self.workbook.get_sheet(sheet_map['Submission'])
        wrt_cell_keep_style(True, sh, 8, 2)
        