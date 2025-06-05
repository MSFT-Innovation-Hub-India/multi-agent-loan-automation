CREATE TABLE Master_Customer_Data (
    Customer_ID VARCHAR(20) PRIMARY KEY,
    Name VARCHAR(100),
    Fathers_Name VARCHAR(100),
    DOB DATE,
    Age INT,
    Gender VARCHAR(10),
    Marital_Status VARCHAR(20),
    Address TEXT,
    City VARCHAR(50),
    State VARCHAR(50),
    Pincode INT,
    Mobile BIGINT,
    Alternate_Mobile BIGINT,
    Email VARCHAR(100),
    PAN VARCHAR(20),
    Aadhaar BIGINT,
    Nationality VARCHAR(50),
    Customer_Since DATE,
    Risk_Category VARCHAR(20),
    Fraud_Flag VARCHAR(20),
    KYC_Status VARCHAR(20),
    Customer_Type VARCHAR(50),
    Annual_Income_Range VARCHAR(50)
);
---------------------------------------------------------------------------------------------------------
CREATE TABLE Employment_Info (
    Customer_ID VARCHAR(20),
    Employment_Type VARCHAR(50),
    Employment_Category VARCHAR(50),
    Employer_Name VARCHAR(100),
    Designation VARCHAR(100),
    Work_Address TEXT,
    Work_Experience_Years INT,
    Monthly_Income INT,
    Other_Income INT,
    Total_Monthly_Income INT,
    Income_Verification VARCHAR(50),
    Employment_Status VARCHAR(50),
    Employer_Contact BIGINT,
    HR_Email VARCHAR(100),
    Joining_Date DATE,
    Previous_Employer VARCHAR(100),
    FOREIGN KEY (Customer_ID) REFERENCES Master_Customer_Data(Customer_ID)
);
---------------------------------------------------------------------------------------------------------
CREATE TABLE Bank_Info (
    Customer_ID VARCHAR(20),
    Bank_Name VARCHAR(100),
    Account_Number VARCHAR(30),
    IFSC VARCHAR(20),
    Account_Type VARCHAR(20),
    Account_Balance DECIMAL(15,2),
    Account_Opening_Date DATE,
    Branch_Name VARCHAR(100),
    Branch_Code VARCHAR(20),
    Relationship_Manager VARCHAR(100),
    Customer_Category VARCHAR(50),
    Debit_Card_Status VARCHAR(20),
    Internet_Banking VARCHAR(20),
    Mobile_Banking VARCHAR(20),
    Average_Monthly_Balance DECIMAL(15,2),
    Account_Status VARCHAR(20),
    FOREIGN KEY (Customer_ID) REFERENCES Master_Customer_Data(Customer_ID)
);
---------------------------------------------------------------------------------------------------------
CREATE TABLE Loan_Info (
    Customer_ID VARCHAR(20),
    Loan_Required VARCHAR(10),
    Loan_Amount INT,
    Loan_Purpose VARCHAR(50),
    EMI DECIMAL(10,2),
    Interest_Rate DECIMAL(5,2),
    Tenure_Months INT,
    Application_Date DATE,
    Loan_Status VARCHAR(50),
    Credit_Score INT,
    Collateral_Required VARCHAR(10),
    Processing_Fee DECIMAL(10,2),
    Loan_Type VARCHAR(50),
    Repayment_Method VARCHAR(50),
    Insurance_Required VARCHAR(10),
    Document_Verifier_ID VARCHAR(50),
    Document_Verifier_Name VARCHAR(100),
    Field_Agent_ID VARCHAR(50),
    Field_Agent_Name VARCHAR(100),
    Bank_Manager_ID VARCHAR(50),
    Bank_Manager_Name VARCHAR(100),
    Loan_Officer_ID VARCHAR(50),
    Loan_Officer_Name VARCHAR(100),
    FOREIGN KEY (Customer_ID) REFERENCES Master_Customer_Data(Customer_ID)
);
---------------------------------------------------------------------------------------------------------
CREATE TABLE Transaction_History (
    Customer_ID VARCHAR(20),
    Transaction_Date DATE,
    Transaction_Type VARCHAR(20),
    Amount DECIMAL(10,2),
    Description TEXT,
    Transaction_ID VARCHAR(30),
    Channel VARCHAR(50),
    Status VARCHAR(20),
    FOREIGN KEY (Customer_ID) REFERENCES Master_Customer_Data(Customer_ID)
);
---------------------------------------------------------------------------------------------------------
CREATE TABLE Audit_Log (
    Customer_ID VARCHAR(20),
    Audit_Date DATE,
    Audit_Type VARCHAR(100),
    Audit_Status VARCHAR(50),
    Auditor_ID VARCHAR(50),
    Auditor_Name VARCHAR(100),
    Remarks TEXT,
    Follow_Up_Required VARCHAR(10),
    Risk_Score INT,
    Next_Review_Date DATE,
    FOREIGN KEY (Customer_ID) REFERENCES Master_Customer_Data(Customer_ID)
);
---------------------------------------------------------------------------------------------------------
CREATE TABLE Bank_Employees (
    Employee_ID VARCHAR(50) PRIMARY KEY,
    Name VARCHAR(100),
    Role VARCHAR(50),
    Email VARCHAR(100),
    Phone BIGINT,
    Branch VARCHAR(100),
    Employee_Code VARCHAR(20),
    Department VARCHAR(50)
);
