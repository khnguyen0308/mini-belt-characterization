#include <math.h>
#include "goertzel.h"

/*
typedef struct {
	float y, d1, d2;
	float f,Fs;
	float reCoeff, imCoeff, aCoeff;
	float R,X;
} goertzel_struct;

typedef struct {
	float M, Phi;

} goertzel_struct_singlesideres;*/

void goertzel_init2(int k, int N, goertzel_struct* g) {
	g->y = 0;
	g->d1 =0;
	g->d2 = 0;
	g->f = k;
	g->Fs = N;
	g->reCoeff = cosf(2*pi*k/N);
	g->imCoeff = sinf(2*pi*k/N);
	//g->reCoeff = arm_cos_f32(2*pi*k/N);
	//g->imCoeff = arm_sin_f32(2*pi*k/N);
	g->aCoeff = g->reCoeff*2;
}


void goertzel_init(double f, double Fs, goertzel_struct* g) {
	g->y = 0;
	g->d1 =0;
	g->d2 = 0;
	g->f = f;
	g->Fs = Fs;
	g->reCoeff = cosf((float)(2*pi*f/Fs));
	g->imCoeff = sinf((float)(2*pi*f/Fs));
	//g->reCoeff = arm_cos_f32((float)(2*pi*f/Fs));
	//g->imCoeff = arm_sin_f32((float)(2*pi*f/Fs));
	g->aCoeff = g->reCoeff*2;
}

void goertzel(goertzel_struct* g, float x) {
	//g->d2 = g->d1 + 0;
	//g->d1 = g->y + 0;
	g->y = x + g->aCoeff * g->d1 - g->d2; //y = x + a*x[-1] - x[-2]
	g->d2 = g->d1+0;
	g->d1 = g->y + 0;
}

/*void goertzel_end(goertzel_struct* g) {
	g->R = g->y - g->reCoeff * g-> d1;
	g->X = g->d2 * g->imCoeff;
}*/

void goertzel_end(goertzel_struct* g, goertzel_struct_singlesideres* g1, int N) { //N is number of samples
	//goertzel_end(g);
	g->R = g->d1 * g->reCoeff - g->d2;
		g->X = g->d1 * g->imCoeff;
	g1->M = sqrtf(g->R * g->R  + g->X * g->X ) / N * 2;
	g1->Phi = atan2f(g->X,g->R)+pi/2;
	//g1->Phi = atan(g->X/g->R)+pi/2;
}
