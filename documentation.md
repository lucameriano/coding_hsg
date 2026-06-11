# Project Overview

This projects consists of a limit order book simulation and a prediction of the 1-minute future return direction. The core components are order matching, a decision making process for the market participants and the training and evaluation loop for prediction models.

# Core Concepts
A limit order book, roughly speaking, lists the offers of market participants on a buying side (bid) and a selling side (ask). A limit order is an order of a quantity at a worst price a participant is willing to conduct an exchange. A market order on the other hand is an order to conduct an exchange of a certain quantity irrespective of the price.

The limit order book contains different price levels and associated quantities of a financial asset. The difference between the best bid price and the best ask price is called the bid/ask spread. The average of the two prices is the mid-price.

For this project the following convention will get used:
If a limit buy order arrives and is higher or equal to the best ask (selling)  price, an exchange will take place. In this exchange the best ask price will be used.
For an arriving limit sell order the limit price will need to be lower or equal to the best bid (buying) price for an exchange to occur, in which case the best bid price will be used. In both cases the price of the exchange will be either at the limit or more favourable from the perspective of the market participant who is placing the order.

More information: https://www.machow.ski/posts/2021-07-18-introduction-to-limit-order-books/

# System Architecture
Data flow: 
`orders.py` contains the functions `match_order` and `cancel_limit_order`. 


The trades, state of the orderbook and the mid-price data will be collected