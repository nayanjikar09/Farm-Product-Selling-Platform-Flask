-- Create the database
CREATE DATABASE IF NOT EXISTS farming_db;

-- Use the created database
USE farming_db;

-- Table to store test data
CREATE TABLE Test (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100)
);

-- Table to store farming types
CREATE TABLE Farming (
    fid INT AUTO_INCREMENT PRIMARY KEY,
    farmingtype VARCHAR(100) UNIQUE NOT NULL
);

-- Table to store agro products
CREATE TABLE Addagroproducts (
    username VARCHAR(50),
    email VARCHAR(50),
    pid INT AUTO_INCREMENT PRIMARY KEY,
    productname VARCHAR(100) NOT NULL,
    productdesc VARCHAR(300),
    price INT
);

-- Table to store user-triggered actions
CREATE TABLE Trig (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fid VARCHAR(100),
    action VARCHAR(100),
    timestamp VARCHAR(100)
);

-- Table to store user information
CREATE TABLE User (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(1000) NOT NULL
);

-- Table to register farmers
CREATE TABLE Register (
    rid INT AUTO_INCREMENT PRIMARY KEY,
    farmername VARCHAR(50) NOT NULL,
    adharnumber VARCHAR(50) NOT NULL,
    age INT NOT NULL,
    gender VARCHAR(50),
    phonenumber VARCHAR(50),
    address VARCHAR(50),
    farming VARCHAR(50),
    FOREIGN KEY (farming) REFERENCES Farming(farmingtype) ON DELETE SET NULL
);

-- Example insertion for Farming table
INSERT INTO Farming (farmingtype) VALUES
('Organic Farming'),
('Hydroponics'),
('Aquaponics');

-- Test the connection
SELECT * FROM Test;
