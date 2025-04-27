import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import pywt
import seaborn as sns
import scikit_posthocs as sp

from scipy import signal
from scipy import stats
from scipy.stats import skew
from scipy.stats import tukey_hsd
from pywt import wavedec
from numpy.core.function_base import linspace

class myVFCDM:
    @staticmethod
    def __myround(n):
        if round(n + 1) - round(n) == 1:
            return float(round(n))
        return n + abs(n) / n * 0.5
    @staticmethod
    def __cdmv(y1, f0, B):
        WB = int(B.shape[0])
        WB1 = int(myVFCDM.__myround((WB-1)*0.5))

        N = int(y1.shape[0])


        temp = 0
        xt1 = np.zeros(N)
        xt2 = np.zeros(N)

        for i in range(0,N):
            temp = temp + f0[i]
            xt1[i] = y1[i] * 2 * math.cos(-2*math.pi*temp)
            xt2[i] = y1[i] * 2 * math.sin(-2*math.pi*temp)



        x1 = np.zeros([(WB1*2 + N)])
        x2 = np.zeros([(WB1*2 + N)])

        x1[(WB1):(-WB1)] = xt1
        x2[(WB1):(-WB1)] = xt2

        cc1 = signal.lfilter(B,1,x1)
        ss1 = signal.lfilter(B,1,x2)
        c1 = cc1[WB-1:N+WB-1]
        s1 = ss1[WB-1:N+WB-1]

        xx= np.sqrt(c1**2+s1**2)
        fai = np.zeros(N)

        for i in range(0,N):
            if c1[i] == 0:
                fai[i] = math.pi * 0.5
            elif c1[i] > 0:
                fai[i] = math.atan(s1[i] / c1[i])
            else:
                fai[i] = math.atan(s1[i] / c1[i]) + math.pi

        return xx,fai

    @staticmethod
    def __angle(h):
        return math.atan2(np.imag(h),np.real(h))

    @staticmethod
    def __instfreq(x):
        N = x.shape[0]
        t = np.zeros(N-2)



        fnormhat = np.zeros(N-2)
        for i in range(0,N-2):
            t[i] = i + 2
            # fnormhat(i) = 0.5*(__angle(-x(t(i)+1)*conj(x(t(i)-1)))+pi)/(2*pi);

            fnormhat[i] = 0.5 * (myVFCDM.__angle(-x[int(t[i])] * np.conj(x[int(t[i]-2)])) + np.pi) / (2*np.pi)
            #print(fnormhat[i])

        return fnormhat, t
    @staticmethod
    def __getMidFreq(Fin):
        Fout = np.zeros(Fin.shape[0])
        for i in range(1,Fin.shape[0]):
            Fout[i] = (Fin[i] + Fin[i-1]) * 0.5
        Fout[0] = Fin[0]
        return Fout
    @staticmethod
    def __getTFRparam(x,freq,B,B1,fw):
        N = x.shape[0]
        dsx = np.zeros(N)
        dsxv = np.zeros(N)
        specxv = np.zeros(N-2)
        dx,faix = myVFCDM.__cdmv(x,freq*np.ones(N),B)

        for j in range(0,N):
            dsx[j] = dx[j] * math.cos(2*np.pi*freq*(j+1)+faix[j])

        dsx1=signal.hilbert2(dsx)
        dsx1 = dsx1[0][:]
        f,_ = myVFCDM.__instfreq(dsx1)
        f = myVFCDM.__getMidFreq(f)

        Ftemp = np.zeros(N)
        for j in range(0,N-2):
            Ftemp[j+1] = f[j]
            if f[j] <= freq - fw:
                Ftemp[j+1] = freq - fw
            if f[j] >= freq + fw:
                Ftemp[j+1] = freq + fw
        Ftemp[0] = Ftemp[1]
        Ftemp[N-1] = Ftemp[N-2]

        dxv,faixv = myVFCDM.__cdmv(x,Ftemp,B1)

        ftemp = 0
        for j in range(0,N):
            ftemp = ftemp + Ftemp[j]
            dsxv[j] = dxv[j] * math.cos(2*np.pi*ftemp+faixv[j])
        dsx1v = signal.hilbert2(dsxv)
        dsx1v = dsx1v[0][:]
        fva,_ = myVFCDM.__instfreq(dsx1v)
        fva = myVFCDM.__getMidFreq(fva)

        for j in range(0,N-2):
            specxv[j] = np.abs(dsx1v[j+1])**2
        return fva,specxv,dsx,dsxv
    @staticmethod
    def __constructR(freq,fva,specxv,fw,N):
        sply = 256
        R = np.zeros([sply,N-2])
        for i in range(0,freq.shape[0]):
            for j in range(0,N-2):
                ftemp = fva[i,j]
                if not (ftemp <= freq[i] - fw or ftemp >= freq[i] + fw):
                    ftempIdx = np.floor(ftemp*2*(sply-1))
                    if ftempIdx <= sply:
                        R[int(ftempIdx),j] = (np.sqrt(R[int(ftempIdx),j]) + np.sqrt(specxv[i,j])) ** 2



        return R


    @staticmethod
    def do(x,Nw,fw):
        assert len(x.shape) == 1 # x has to be 1D signal
        N = x.shape[0]
        fv = fw * 0.5
        B = signal.firwin(Nw+1,fw * 2)
        B1 = signal.firwin(Nw+1,fv* 2)

        ftemp = 0
        freq = []
        while ftemp <= 0.5-fw:
            freq.append(ftemp)
            ftemp = ftemp + 2*fw


        freq = np.array(freq)


        dx,faix = myVFCDM.__cdmv(x,np.zeros(N),B)

        dx = dx * 0.5
        dsx = np.zeros(N)
        for j in range(0,N):
            dsx[j] = dx[j] * math.cos(faix[j])

        dsx1 = signal.hilbert2(dsx)
        #dsx1 = np.conj(dsx1[0][:])
        dsx1 = dsx1[0][:]

        f,_ = myVFCDM.__instfreq(dsx1)

        specx = np.zeros(N-2)
        for i in range(0,N-2):
            specx[i] = np.abs(dsx1[i+1])**2


        ## VFCDM
        fva = np.zeros([freq.shape[0], N-2])
        specxv = np.zeros([freq.shape[0], N-2])

        fva[0,:] = myVFCDM.__getMidFreq(f)
        specxv[0,:] = specx

        for i in range(1,freq.shape[0]):
            fva[i,:], specxv[i,:],_,_ = myVFCDM.__getTFRparam(x,freq[i],B,B1,fw)

        R1 = myVFCDM.__constructR(freq,fva,specxv,fw,N)

        ######################################
        ftemp = fw
        freq1 = []
        while ftemp <= 0.5-fw:
            freq1.append(ftemp)
            ftemp = ftemp + 2*fw
        freq1 = np.array(freq1)
        fva = np.zeros([freq1.shape[0], N-2])
        specxv = np.zeros([freq1.shape[0], N-2])


        comp1 = np.zeros([x.shape[0],freq1.shape[0]])
        comp2 = np.zeros([x.shape[0],freq1.shape[0]])

        for i in range(0,freq1.shape[0]):
            fva[i,:], specxv[i,:],comp1[:,i],comp2[:,i] = myVFCDM.__getTFRparam(x,freq1[i],B,B1,fw)

        R2 = myVFCDM.__constructR(freq1,fva,specxv,fw,N)


        sply = 256
        R = R1
        for i in range(0,freq1.shape[0]):
            for ff in range(int(np.floor((freq1[i]-fw/2)*2*(sply-1))) , int(np.floor((freq1[i]+fw/2)*2*(sply-1)))):
                for j in range(0, N-2):
                    R[ff,j] = R2[ff,j]

        return R, comp1, comp2, freq1
    
def extract_vfccdm(signal, filter_length, fs):
    
    # Create VFCDM Object
    vfcdm = myVFCDM()

    X, comp1, comp2, freq = vfcdm.do(signal, filter_length, 1/fs)

    return comp1

