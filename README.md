# Employee Purchase
This Odoo module solves a use case where:
* On a company there are internal users, managers, and employees.
* Employees can request for the product that company offers aligned with the vendors.
* Employee will have some restrictions while requesing the products:
  * Maximum amount of an item that he/she can request
  * Product Category that they are whitelisted to request
  * If a request from the same month was rejected earlier, then he/she will have to wait till next month to make another request.
* Employee can make the product request from the portal.
* Employee's request can be either approved/rejected by his/her manager
  * If rejected, he/she will not be allowed to make another request until the next month
* Upon approval of the request, Employee can buy the product.
* A Puchase order will be created for the order and processed until the product is received on the office.
* Then an internal employee will mark the order as ready-to-pickup
* Once the employee picks his/her item, the internal user will mark the order as done.

# How to Setup
* Clone the repository
* Goto the directory and on the the terminal enter (you need to have docker installed):
'''
docker-compose up
'''
* Create an odoo database (donot load demo data)
* Install the module "Employee Purchase"
* For the demonstration of the module (Test case 2021), I have already created all required datas.

### Sample Employees:
* Email: saurav@example.com
* Password: 1

* Email: ram@example.com
* Password: 1

### Sample Manager:
* Email: sam@example.com
* Password: 1

### Sample Internal User:
* Email: tim@example.com
* Password: 1

You may immediately begin Demonstration!