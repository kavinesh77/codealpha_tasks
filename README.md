# Data Redundancy Removal System

A cloud-based data validation and duplicate detection system developed using Python, Flask, and MongoDB Atlas.

## Project Objective

The system identifies redundant or duplicate data before storing it in the database. It validates new records against existing records and allows only unique and verified records to be stored.

## Features

- Data validation
- Duplicate data detection
- Redundant data identification
- Duplicate prevention
- Unique record verification
- MongoDB Atlas cloud database
- Web-based dashboard
- Search and record management
- Phone and email based duplicate checking

## Technologies Used

- Python
- Flask
- MongoDB Atlas
- PyMongo
- HTML
- CSS
- JavaScript

## System Workflow

1. User enters new data.
2. The system validates the input.
3. The new record is compared with existing records.
4. The system classifies the record.
5. Duplicate records are rejected.
6. Unique and verified records are stored in MongoDB Atlas.
7. Verified records can be viewed through the dashboard.

## Classification

### UNIQUE
The record is new and verified, so it is added to the database.

### DUPLICATE
The record already exists in the database, so it is not added again.

### POSSIBLE_DUPLICATE
The record is sufficiently similar to an existing record and requires further checking.

### FALSE_POSITIVE
The system determines that a similarity does not represent an actual duplicate.

## Database

MongoDB Atlas is used as the cloud database.

The application stores verified records and prevents duplicate entries using database indexes and validation logic.

## Installation

Clone the repository:

```bash
git clone https://github.com/kavinesh77/codealpha_tasks.git
cd codealpha_tasks
