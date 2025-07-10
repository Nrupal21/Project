-- PostgreSQL database schema for Guides Travel Platform
-- This file contains the complete schema definition for the application

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================
-- USERS AND AUTHENTICATION
-- =============================================

-- Custom User Table (extends Django's auth_user)
CREATE TABLE IF NOT EXISTS accounts_customuser (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE,
    is_superuser BOOLEAN NOT NULL DEFAULT false,
    username VARCHAR(150) NOT NULL UNIQUE,
    email VARCHAR(254) NOT NULL UNIQUE,
    is_staff BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    date_joined TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    phone_number VARCHAR(20) DEFAULT '',
    is_verified BOOLEAN NOT NULL DEFAULT false,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    first_name VARCHAR(30) DEFAULT '',
    last_name VARCHAR(150) DEFAULT ''
);

-- User Profile Table
CREATE TABLE IF NOT EXISTS accounts_userprofile (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES accounts_customuser(id) ON DELETE CASCADE,
    date_of_birth DATE,
    profile_picture TEXT,
    bio TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- User Preferences Table
CREATE TABLE IF NOT EXISTS accounts_userpreferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES accounts_customuser(id) ON DELETE CASCADE,
    preferred_currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    language VARCHAR(2) NOT NULL DEFAULT 'en',
    newsletter_subscription BOOLEAN NOT NULL DEFAULT true,
    marketing_emails BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- DESTINATIONS
-- =============================================

-- Regions Table
CREATE TABLE IF NOT EXISTS destinations_region (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    image VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT true,
    "order" INTEGER DEFAULT 0,
    code VARCHAR(10)
);

-- Destinations Table
CREATE TABLE IF NOT EXISTS destinations_destination (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    region_id UUID NOT NULL REFERENCES destinations_region(id) ON DELETE CASCADE,
    slug VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    short_description TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    address TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_featured BOOLEAN NOT NULL DEFAULT false
);

-- =============================================
-- TOURS
-- =============================================

-- Tours Table
CREATE TABLE IF NOT EXISTS tours_tour (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    short_description TEXT,
    duration_days INTEGER NOT NULL DEFAULT 1,
    max_group_size INTEGER,
    difficulty VARCHAR(20) NOT NULL DEFAULT 'moderate',
    price DECIMAL(10, 2) NOT NULL,
    price_discount DECIMAL(10, 2) DEFAULT 0,
    start_location_id UUID REFERENCES destinations_destination(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT true,
    rating_avg DECIMAL(3, 2) DEFAULT 0,
    rating_count INTEGER DEFAULT 0
);

-- Tour Images Table
CREATE TABLE IF NOT EXISTS tours_tourimage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tour_id UUID NOT NULL REFERENCES tours_tour(id) ON DELETE CASCADE,
    image VARCHAR(100) NOT NULL,
    caption VARCHAR(200),
    is_featured BOOLEAN NOT NULL DEFAULT false,
    "order" INTEGER DEFAULT 0
);

-- Tour Dates Table
CREATE TABLE IF NOT EXISTS tours_tourdate (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tour_id UUID NOT NULL REFERENCES tours_tour(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    discount_price DECIMAL(10, 2),
    max_group_size INTEGER,
    current_group_size INTEGER DEFAULT 0,
    is_available BOOLEAN NOT NULL DEFAULT true
);

-- =============================================
-- BOOKINGS
-- =============================================

-- Bookings Table
CREATE TABLE IF NOT EXISTS bookings_booking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES accounts_customuser(id) ON DELETE CASCADE,
    tour_date_id UUID NOT NULL REFERENCES tours_tourdate(id) ON DELETE CASCADE,
    booking_reference VARCHAR(20) NOT NULL UNIQUE,
    num_people INTEGER NOT NULL DEFAULT 1,
    total_amount DECIMAL(10, 2) NOT NULL,
    discount_amount DECIMAL(10, 2) DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    payment_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Booking Guests Table
CREATE TABLE IF NOT EXISTS bookings_bookingguest (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    booking_id UUID NOT NULL REFERENCES bookings_booking(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(254) NOT NULL,
    phone_number VARCHAR(20),
    special_requirements TEXT
);

-- =============================================
-- REVIEWS
-- =============================================

-- Reviews Table
CREATE TABLE IF NOT EXISTS reviews_review (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES accounts_customuser(id) ON DELETE CASCADE,
    tour_id UUID NOT NULL REFERENCES tours_tour(id) ON DELETE CASCADE,
    booking_id UUID REFERENCES bookings_booking(id) ON DELETE SET NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(200) NOT NULL,
    comment TEXT NOT NULL,
    is_approved BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- INDEXES
-- =============================================

-- User Indexes
CREATE INDEX IF NOT EXISTS idx_user_email ON accounts_customuser (email);
CREATE INDEX IF NOT EXISTS idx_user_username ON accounts_customuser (username);
CREATE INDEX IF NOT EXISTS idx_user_role ON accounts_customuser (role);
CREATE INDEX IF NOT EXISTS idx_user_is_active ON accounts_customuser (is_active);

-- Destination Indexes
CREATE INDEX IF NOT EXISTS idx_destination_region ON destinations_destination (region_id);
CREATE INDEX IF NOT EXISTS idx_destination_slug ON destinations_destination (slug);
CREATE INDEX IF NOT EXISTS idx_destination_is_active ON destinations_destination (is_active);
CREATE INDEX IF NOT EXISTS idx_destination_is_featured ON destinations_destination (is_featured);

-- Tour Indexes
CREATE INDEX IF NOT EXISTS idx_tour_slug ON tours_tour (slug);
CREATE INDEX IF NOT EXISTS idx_tour_is_active ON tours_tour (is_active);
CREATE INDEX IF NOT EXISTS idx_tour_rating ON tours_tour (rating_avg);
CREATE INDEX IF NOT EXISTS idx_tour_price ON tours_tour (price);

-- Booking Indexes
CREATE INDEX IF NOT EXISTS idx_booking_user ON bookings_booking (user_id);
CREATE INDEX IF NOT EXISTS idx_booking_tour_date ON bookings_booking (tour_date_id);
CREATE INDEX IF NOT EXISTS idx_booking_status ON bookings_booking (status);
CREATE INDEX IF NOT EXISTS idx_booking_payment_status ON bookings_booking (payment_status);
CREATE INDEX IF NOT EXISTS idx_booking_reference ON bookings_booking (booking_reference);

-- Review Indexes
CREATE INDEX IF NOT EXISTS idx_review_user ON reviews_review (user_id);
CREATE INDEX IF NOT EXISTS idx_review_tour ON reviews_review (tour_id);
CREATE INDEX IF NOT EXISTS idx_review_rating ON reviews_review (rating);
CREATE INDEX IF NOT EXISTS idx_review_is_approved ON reviews_review (is_approved);

-- =============================================
-- FUNCTIONS AND TRIGGERS
-- =============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply the trigger to all tables with updated_at column
DO $$
DECLARE
    t record;
BEGIN
    FOR t IN 
        SELECT table_name 
        FROM information_schema.columns 
        WHERE column_name = 'updated_at' 
        AND table_schema = 'public'
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS update_%s_modtime ON %I', 
                      t.table_name, t.table_name);
        EXECUTE format('CREATE TRIGGER update_%s_modtime
                      BEFORE UPDATE ON %I
                      FOR EACH ROW EXECUTE FUNCTION update_modified_column()',
                      t.table_name, t.table_name);
    END LOOP;
END$$;

-- Function to update tour rating when a new review is added
CREATE OR REPLACE FUNCTION update_tour_rating()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE tours_tour
    SET 
        rating_avg = (
            SELECT AVG(rating) 
            FROM reviews_review 
            WHERE tour_id = NEW.tour_id 
            AND is_approved = true
        ),
        rating_count = (
            SELECT COUNT(*) 
            FROM reviews_review 
            WHERE tour_id = NEW.tour_id 
            AND is_approved = true
        )
    WHERE id = NEW.tour_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for review updates
CREATE TRIGGER update_tour_rating_trigger
AFTER INSERT OR UPDATE OR DELETE ON reviews_review
FOR EACH ROW
EXECUTE FUNCTION update_tour_rating();

-- Function to update current group size when a booking is made
CREATE OR REPLACE FUNCTION update_tour_group_size()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        UPDATE tours_tourdate
        SET current_group_size = current_group_size + NEW.num_people
        WHERE id = NEW.tour_date_id;
    END IF;
    
    IF TG_OP = 'DELETE' OR TG_OP = 'UPDATE' THEN
        UPDATE tours_tourdate
        SET current_group_size = current_group_size - OLD.num_people
        WHERE id = OLD.tour_date_id;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for booking updates
CREATE TRIGGER update_group_size_trigger
AFTER INSERT OR UPDATE OR DELETE ON bookings_booking
FOR EACH ROW
EXECUTE FUNCTION update_tour_group_size();

-- Function to generate booking reference
CREATE OR REPLACE FUNCTION generate_booking_reference()
RETURNS TRIGGER AS $$
DECLARE
    ref text;
    suffix text;
    counter integer := 1;
BEGIN
    -- Generate a random 6-character string
    ref := upper(substring(md5(random()::text) from 1 for 6));
    
    -- Check for duplicates and append a counter if needed
    WHILE EXISTS (SELECT 1 FROM bookings_booking WHERE booking_reference = ref) LOOP
        suffix := counter::text;
        ref := upper(substring(md5(random()::text) from 1 for 6 - length(suffix))) || suffix;
        counter := counter + 1;
    END LOOP;
    
    NEW.booking_reference := ref;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for booking reference generation
CREATE TRIGGER generate_booking_reference_trigger
BEFORE INSERT ON bookings_booking
FOR EACH ROW
EXECUTE FUNCTION generate_booking_reference();
