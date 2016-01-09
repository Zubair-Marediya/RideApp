from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
previousrides = Table('previousrides', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('rider_name', String(length=100)),
    Column('driver_name', String(length=100)),
    Column('meeting_place_latitude', Float),
    Column('meeting_place_longitude', Float),
)

todaystable = Table('todaystable', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String(length=100)),
    Column('phone_number', String(length=10)),
    Column('res_latitude', Float),
    Column('res_longitude', Float),
    Column('rider_or_driver', String(length=6)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['previousrides'].create()
    post_meta.tables['todaystable'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['previousrides'].drop()
    post_meta.tables['todaystable'].drop()
