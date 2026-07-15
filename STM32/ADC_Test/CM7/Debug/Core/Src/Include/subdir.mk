################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (14.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Core/Src/Include/goertzel.c 

OBJS += \
./Core/Src/Include/goertzel.o 

C_DEPS += \
./Core/Src/Include/goertzel.d 


# Each subdirectory must supply rules for building sources it contributes
Core/Src/Include/%.o Core/Src/Include/%.su Core/Src/Include/%.cyclo: ../Core/Src/Include/%.c Core/Src/Include/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m7 -std=gnu11 -g3 -DDEBUG -DARM_MATH_CM7 -DCORE_CM7 -DUSE_HAL_DRIVER -DSTM32H755xx -DUSE_PWR_DIRECT_SMPS_SUPPLY -DARM_MATH_MATRIX_CHECK -DARM_MATH_ROUNDING -D__FPU_PRESENT=1 -c -I"D:/TUChemnitz/2.Sem/1.Project_Lab_Embedded_Systems/mini-belt-characterization/STM32/ADC_Test/CM7/Core/Src/Include" -I../Core/Inc -I../../Drivers/STM32H7xx_HAL_Driver/Inc -I../../Drivers/STM32H7xx_HAL_Driver/Inc/Legacy -I../../Drivers/BSP/STM32H7xx_Nucleo -I../../Drivers/CMSIS/Device/ST/STM32H7xx/Include -I../../Drivers/CMSIS/Include -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv5-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Core-2f-Src-2f-Include

clean-Core-2f-Src-2f-Include:
	-$(RM) ./Core/Src/Include/goertzel.cyclo ./Core/Src/Include/goertzel.d ./Core/Src/Include/goertzel.o ./Core/Src/Include/goertzel.su

.PHONY: clean-Core-2f-Src-2f-Include

