# Report

## Design Decisions

### 1. Layout Design
The layout enables users to navigate quickly to any interface. Therefore, it requires a tab bar for navigation. Using Flask's template syntax and Bootstrap classes, I implemented this feature. By adding conditional statements to each navigation link, the current URL is checked to highlight the current page with the `active` class.

Additionally, there is a footer that describes "All rights reserved."

### 2. Home Page Design
The homepage's role is to navigate users to the functions they want. Therefore, I placed a list-based navigation menu.

### 3. Add/Edit Booking Design
The Booking function allows users to submit a form for reservations. Since bookings can only be made for existing users, I added a button that navigates to `addcustomer` to add new users.

1.	Check if a specific customer has duplicate bookings on a specific date:
	
  •	For each booking night, query the bookings table to see if there is already a record with the same customer and booking_date.
	
  •	If such a record exists, return an error page indicating that the customer already has a booking on that date.

	2.	Check if the site is fully booked on a specific date:
	
  •	Query the bookings table for all records with the same site and booking_date, and calculate the total occupancy.
	
  •	Query the sites table for the maximum occupancy of the given site_id.
	
  •	If the existing total occupancy plus the new occupancy exceeds the site’s capacity on that date, return an error page indicating that the site cannot accommodate more people on that date.

	3.	Insert booking records for each night:
	
  •	For each booking night, insert a booking record into the bookings table.



### 4. Campers Design
The campers design is straightforward, requiring only a date for querying.

### 5. Search Customers
I used a table to display the search results. Considering that real-world scenarios might yield a large number of search results, I implemented pagination. When `searchquery` has a value, the data is displayed based on `searchquery` and `page` at `Customer List`. If not, the `searchcustomers` interface is displayed.

### 6. Summary Report
I have placed the entry point for this page within the `Customer List`, making it convenient to view specific user information after searching. The design allows for receiving parameters, enabling direct navigation to detailed content after adding, modifying, or completing a booking.

### 6. Message Prompt
I added a success page to notify users of successful bookings, with a button to return to the homepage. Considering that the success prompt can be reused, I allowed this page to accept a `message` text to display the prompt information.

Similarly, I designed an error page based on the same principle.

### 7. Enhancing Website Usability
To enhance usability, I added a button on the success page that allows users to jump directly to the customer details page after completing a booking, editing, or adding operation. The button is hidden when there is no `customer_id`. In the `success.html` template, conditional statements are used to control the display of the button.



## Database Questions

### 1. SQL Statement to Create the Customer Table

The SQL statement that creates the `customers` table and defines its fields/columns is:

```sql
CREATE TABLE IF NOT EXISTS `customers` (
  `customer_id` INT NOT NULL AUTO_INCREMENT,
  `firstname` VARCHAR(45) NULL,
  `familyname` VARCHAR(60) NOT NULL,
  `email` VARCHAR(255) NULL,
  `phone` VARCHAR(12) NULL,
  PRIMARY KEY (`customer_id`)
);
```

### 2. SQL Line Setting Up the Relationship Between the Customer and Booking Tables

The line of SQL code that sets up the relationship between the `customers` and `bookings` tables is:

```sql
CONSTRAINT `customer`
  FOREIGN KEY (`customer`)
  REFERENCES `customers` (`customer_id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION
```

###  3. SQL Lines to Insert Details into the Sites Table

The lines of SQL code that insert details into the `sites` table are:

```sql
INSERT INTO `sites` (`site_id`, `occupancy`) VALUES ('P1', '5');
INSERT INTO `sites` (`site_id`, `occupancy`) VALUES ('P4', '2');
INSERT INTO `sites` (`site_id`, `occupancy`) VALUES ('P2', '3');
INSERT INTO `sites` (`site_id`, `occupancy`) VALUES ('P5', '8');
INSERT INTO `sites` (`site_id`, `occupancy`) VALUES ('P3', '2');
INSERT INTO `sites` (`site_id`, `occupancy`) VALUES ('U1', '6');
INSERT INTO `sites` (`site_id`, `occupancy`) VALUES ('U2', '2');
INSERT INTO `sites` (`site_id`, `occupancy`) VALUES ('U3', '4');
INSERT INTO `sites` (`site_id`, `occupancy`) VALUES ('U4', '4');
INSERT INTO `sites` (`site_id`, `occupancy`) VALUES ('U5', '2');
```

###  4. Audit Trail: Adding Timestamp to Booking Table

To record the time and date a booking was added to the database, you would need to add the following column to the `bookings` table:

**Table Name**: `bookings`  
**New Column Name**: `created_at`  
**Data Type**: `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`

###  5. Changes Needed for Customers to Make Their Own Bookings

To allow customers to make their own bookings, the data model would need the following changes:

### Add User Authentication Fields

**Table Name**: `customers`  
**New Column Names and Data Types**:
- `username` VARCHAR(50) NOT NULL UNIQUE
- `password_hash` VARCHAR(255) NOT NULL

These fields would store the login credentials for the customers.

### Booking Confirmation and Status

**Table Name**: `bookings`  
**New Column Names and Data Types**:
- `status` ENUM('pending', 'confirmed', 'cancelled') DEFAULT 'pending'
- `confirmation_code` VARCHAR(50) NULL
