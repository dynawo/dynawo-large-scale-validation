# ANALYSIS OF SHAP VALUES

## CONSTR_GEN_Q
An accumulation of points near zero is evident, but drawing definitive conclusions is challenging. Values greater than 0 show a subtle tendency to increase the Shap value, indicating an increase in the final target.

## TAP CHANGERS
There is a noticeable inclination for the Shap value to rise as the variable value increases. This suggests that a higher number of taps changed in the powerflow simulation leads to a more distinct second simulation compared to the first.

## CONSTR_VOLT
In this variable, a pattern emerges where, in most cases, a non-zero variable value corresponds to an increased Shap value. Consequently, there is a greater difference between the dynamic simulation and the powerflow.

## N_ITER
No clear trend is observed for this Shap value concerning the final target. However, it is closely linked to the variable CONSTR_GEN_Q, indicating that higher values of CONSTR_GEN_Q lead to more iterations.

## AFFECTED_ELEM
For the number of elements affected by the contingency, a slight increase in the Shap value or target is noticeable as the variable increases, though some points deviate from this general trend.

## COEF_REPORT
While the GBM model identifies it as an important variable, there are no apparent linear patterns to determine its behavior at first glance.

## MAX_FLOW
Contrary to previous observations, higher values of this parameter are generally associated with Shap values equal to 0, indicating no increase in the final target. It correlates with the MAX_VOLT variable—higher values of one correspond to higher values of the other.

## MIN_VOLT
A clear tendency is observed in this variable—values greater than zero lead to an increase in the Shap value as the characteristic value rises. It correlates with the MAX_VOLT variable, with higher values of one corresponding to higher values of the other.

## MAX_VOLT
A clear tendency is observed in this variable—values greater than zero lead to an increase in the Shap value as the characteristic value rises.

## RES_NODE
No clear signal is observed for values larger than zero in this characteristic. However, for values close to 0, the distance between the results of the two simulations tends to decrease.

## CONSTR_FLOW
For this variable, no clear signal is observed for values larger than zero. However, for values close to 0, it does not contribute significantly to the difference between the dynamic simulation and the larger loadflow.
