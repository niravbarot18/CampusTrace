# Lost & Found System Automation

### Smart Campus Lost & Found Management System

A desktop-based Lost & Found Management System built using **Python**, **Tkinter**, and **SQLite** to streamline reporting, tracking, and claiming of lost and found items within a campus environment.

---

## Features

* Report Lost & Found items
* Upload item images
* Search and filter items
* Claim found items with proof upload
* Admin claim approval/rejection system
* Integrated Admin ↔ User chat system
* SQLite database integration
* Image preview support

---

## Tech Stack

* Python
* Tkinter
* SQLite
* Pillow (PIL)

---

## Database Tables

| Table         | Purpose                   |
| ------------- | ------------------------- |
| `lost_items`  | Stores lost item reports  |
| `found_items` | Stores found item reports |
| `claims`      | Stores claim requests     |
| `messages`    | Stores chat messages      |

---

## Installation

### Install Dependencies

```bash
pip install pillow
```

### Run the Application

```bash
python "Lost&Found.py"
```

On first launch, the system automatically creates:

* `trackmystuff.db`
* `images/`
* `proofs/`

---

## System Modules

### Report Lost Item

Users can submit:

* Item details
* Location
* Date
* Contact information
* Optional image upload

### Report Found Item

Store found item information with image support.

### Search Items

* Search by keyword
* Filter Lost / Found / All
* Preview item images
* Delete records
* Claim found items

### Claim Management

Users can:

* Submit ownership claims
* Upload proof images
* Add verification details

Admins can:

* Approve or reject claims
* View proof images
* Delete claims
* Manage item return status

### Chat System

Integrated claim-based chat system between:

* Admin
* User

All messages are stored with timestamps.

---

## Future Enhancements

* User authentication
* Email notifications
* Cloud database integration
* AI-based item matching
* Web application deployment
