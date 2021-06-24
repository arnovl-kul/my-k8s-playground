# Clear workspace
rm(list = ls())

# Import packages
library("reshape2")
library("ggplot2")
library("gridExtra")
library("plyr")
library(mosaic)
library(mosaicCore)
library(mosaicData)
library(mosaicCalc)
library(data.table)

# Directory of r-file
setwd("/home/arno/docker-thesis/r/")

x=read.csv(file="/home/arno/Documents/res/summary_linear.csv", header = TRUE) 

avg_cpu = unlist(x["Avg.CPU"])
tenants = unlist(x["Tenants"])

cpu_request = avg_cpu*tenants*250
cpu_limit = tenants*250

frame=data.frame(tenants, cpu_limit, cpu_request)

plotPoints(cpu_limit~tenants, main="Linear", xlim=c(0,20))
plotPoints(cpu_request~tenants, add=TRUE, col="red")

fl1 = fitModel(cpu_limit~A*tenants + B, data = frame)
fl2 = fitModel(cpu_request~A*tenants + B, data = frame)

#plotFun(fl1(tenants)~tenants, add=TRUE, col="blue")
plotFun(fl2(tenants)~tenants, add=TRUE, col="red")

